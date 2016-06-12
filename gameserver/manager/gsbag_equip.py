#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from time     import time
from log      import log
from errorno  import *
from constant import *
from json     import loads, dumps
from utils    import get_previous_value, datetime2string

from syslogger              import syslogger
from twisted.internet       import defer
from system                 import get_item_by_itemid, get_equip_strengthen_cost, \
        get_equip_crit_conf, get_equip_refine_levels, get_equip_refine_conf, get_equip_refine_consume, get_open_server_quest_conf

from manager.gsattribute    import GSAttribute

EQUIP_POSITION_TYPEs = {2: ITEM_TYPE_HELMET,
                        3: ITEM_TYPE_WEAPON,
                        4: ITEM_TYPE_NECKLACE,
                        5: ITEM_TYPE_ARMOR}

class GSBagEquipMgr(object):
    '''
    @summary: 玩家道具背包
    @param  : refine_attribute-json对象 format: [[attrib_id, attribute_value, max_value], ...]
    @param  : camp_id范围1-6, 
    @param  : position_id范围2-5, 2-头盔 3-武器, 4-项链, 5-护甲
    @param  : refine_cost为消耗的洗炼石数量
    '''
    _table  = 'bag_equip'

    def __init__(self, user):
        '''
        @param: __camp_position format: {camp_id: {position_id: user_equip_id, ...}, ...}, 其中camp_id范围1-6, position_id范围是1-4
        '''
        self.user = user
        self.cid  = user.cid
        self.__gsattribs = None
        # 装备在阵容中的信息 在阵容中新增、替换、卸下装备时需要同时维护
        self.__camp_position = {}

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def _load(self):
        if self.__gsattribs is None:
            if not self.__loading:
                self.__loading = True
                #log.info('For Test. load. self.__gsattribs is None.')
                self.__gsattribs = yield GSAttribute.load( self.cid, GSBagEquipMgr._table )
                for gsattrib in self.__gsattribs.itervalues():
                    # 获取阵容中的装备信息
                    if gsattrib.camp_id > 0:
                        if gsattrib.camp_id in self.__camp_position:
                            _camp_equip = self.__camp_position[gsattrib.camp_id]
                        else:
                            _camp_equip = {}
                            self.__camp_position[gsattrib.camp_id] = _camp_equip
                        if not _camp_equip.has_key(gsattrib.position_id):
                            _camp_equip[gsattrib.position_id] = gsattrib.attrib_id

                for d in self.__defers:
                    d.callback(True)

                self.__loading = False
                self.__defers  = []
            else:
                d = defer.Deferred()
                self.__defers.append(d)
                yield d

    def sync_to_cs(self):
        #log.info('For Test. sync_to_cs equip.......')
        if self.__gsattribs:
            for attrib in self.__gsattribs.itervalues():
                attrib.syncToCS()

    @defer.inlineCallbacks
    def get_item_by_item_id(self, item_id):
        yield self._load()
        for attrib in self.__gsattribs.itervalues():
            if attrib.item_id == item_id:
                defer.returnValue( attrib )
        defer.returnValue( None )

    @defer.inlineCallbacks
    def get(self, user_item_id):
        yield self._load()
        defer.returnValue( self.__gsattribs.get(user_item_id, None) )

    @defer.inlineCallbacks
    def cur_capacity(self):
        yield self._load()
        count = 0
        # 已穿戴的装备不计算在装备背包内
        for attrib in self.__gsattribs.itervalues():
            if attrib.camp_id == 0:
                count += 1
        defer.returnValue( count )

    @property
    @defer.inlineCallbacks
    def value_list(self):
        yield self._load()
        count = 0
        value_list = []
        for attrib in self.__gsattribs.itervalues():
            value_list.append( (attrib.attrib_id, attrib.item_id, attrib.level, loads(attrib.refine_attribute), attrib.refine_cost, attrib.camp_id, attrib.strengthen_cost) )
            # 已穿戴的装备不计算在装备背包内
            if attrib.camp_id == 0:
                count += 1

        defer.returnValue( (count, value_list) )

    def add_new_items(self, new, items=[]):
        ''' new=[uid, type, id, num], 其中num为道具新增的数量 '''
        if not new or len(new) != 4:
            return items

        for _i in items:
            if _i[:3] == new[:3]:
                _i[3] += new[3]
                break
        else:
            items.append( new )

        return items

    @defer.inlineCallbacks
    def new(self, item_id, item_num, way_type=WAY_UNKNOWN, way_others=''):
        yield self._load()
        item_conf = get_item_by_itemid( item_id )
        if not item_conf:
            log.error('Can not find conf. item_id: {0}.'.format( item_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )
        # 检查道具类型
        item_type  = item_conf['ItemType']
        if item_type not in BAG_EQUIP:
            log.error('new. Item type error. item_id: {0}.'.format( item_id ))
            defer.returnValue( (ITEM_TYPE_ERROR, None) )
        # 判断图鉴
        yield self.user.atlaslist_mgr.new_atlaslist(CATEGORY_TYPE_EQUIP, item_type, item_conf['Quality'], item_id)

        time_now   = int(time()) #datetime2string()
        MAX_NUM    = item_conf['MaxOverlyingCount'] or (2 ** 16 - 1)
        new_items  = []
        for attrib in self.__gsattribs.itervalues():
            # 找打未达到MAX_NUM的相同的 item
            if item_type == attrib.item_type and item_id == attrib.item_id and MAX_NUM > attrib.item_num:
                if (attrib.item_num + item_num) <= MAX_NUM:
                    attrib.item_num += item_num
                    new_items = self.add_new_items( [attrib.attrib_id, item_type, item_id, item_num], new_items )
                else:
                    add_num         = MAX_NUM - attrib.item_num
                    item_num        = item_num - add_num
                    attrib.item_num = MAX_NUM
                    new_items = self.add_new_items( [attrib.attrib_id, item_type, item_id, add_num], new_items )
                    continue
                break
        else:
            cur_item_num = item_num
            while cur_item_num >= MAX_NUM:
                res_err, new_attrib = yield self.create_table_data(item_type, item_id, MAX_NUM, time_now)
                if res_err:
                    defer.returnValue( (UNKNOWN_ERROR, None) )
                cur_item_num -= MAX_NUM
                new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, MAX_NUM], new_items )
            else:
                if cur_item_num > 0:
                    res_err, new_attrib = yield self.create_table_data(item_type, item_id, cur_item_num, time_now)
                    if res_err:
                        defer.returnValue( (UNKNOWN_ERROR, None) )
                    new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, cur_item_num], new_items )

        # add syslog
        for _item in new_items:
            syslogger(LOG_ITEM_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _item[0], _item[2], _item[3], way_type, way_others)
        defer.returnValue( (NO_ERROR, new_items) )

    @defer.inlineCallbacks
    def create_table_data(self, item_type, item_id, item_num, time_now, level=0, refine_attribute=[], refine_cost=0, camp_id=0, position_id=0, strengthen_cost=0):
        gsattrib = GSAttribute( self.cid, GSBagEquipMgr._table )
        # refine_attribute 是json格式保存
        res_err  = yield gsattrib.new( cid=self.cid, item_type=item_type, item_id=item_id, item_num=item_num, camp_id=camp_id, position_id=position_id, level=level, strengthen_cost=strengthen_cost, refine_attribute=dumps(refine_attribute), refine_cost=refine_cost, deleted=0, create_time=time_now, update_time=time_now, del_time=0, aux_data='' )
        if res_err:
            log.error('GSBagEquipMgr create table data error. ')
            defer.returnValue( (UNKNOWN_ERROR, None) )

        self.__gsattribs[gsattrib.attrib_id] = gsattrib
        defer.returnValue( (NO_ERROR, gsattrib) )

    def delete_table_data(self, attrib_id):
        if self.__gsattribs.has_key( attrib_id ):
            gsattrib = self.__gsattribs[attrib_id]
            gsattrib.delete()
            del self.__gsattribs[attrib_id]
        else:
            log.error('Can not find delete data. uid: {0}.'.format( attrib_id ))

    @defer.inlineCallbacks
    def get_sell_back_cost(self, *args):
        '''
        @summary: 出售道具时返还消耗的金币
        @param: had_cost-强化到当前等级已消耗的金币总数
        '''
        user_item_ids, = args

        res_err = [UNKNOWN_EQUIP_ERROR, 0]
        for _ueid in user_item_ids:
            attrib  = yield self.get( _ueid )
            if not attrib:
                defer.returnValue( res_err )

            item_conf = get_item_by_itemid( attrib.item_id )
            if not item_conf:
                defer.returnValue( res_err )
            if not item_conf['Price']:
                res_err[0] = ITEM_CANNOT_SELL
                defer.returnValue( res_err )

            res_err[1] += (item_conf['Price'] * attrib.item_num + attrib.strengthen_cost)
            #log.error('For Test. _ueid: {0}, strengthen_cost: {1}, Price: {2}.'.format( _ueid, attrib.strengthen_cost, item_conf['Price'] ))

        for _ueid in user_item_ids:
            self.delete_table_data(_ueid)

        res_err[0] = NO_ERROR
        defer.returnValue( res_err )

    def get_cost_by_level_type(self, next_level, item_id, item_type):
        '''
        @summary: 通过item id, item type, next strengthen level 获取next cost golds数
        '''
        next_cost = 0
        # 强化等级上限为玩家等级的2倍
        if (next_level - 1) >= (self.user.base_att.level * 2):
            log.error('Strengthen level has largest. char level: {0}, equip next level: {1}.'.format( self.user.base_att.level, next_level ))
            return CHAR_LEVEL_LIMIT, next_cost
        # 强化消耗金币conf
        cost_conf = get_equip_strengthen_cost(next_level, item_type)
        if not cost_conf:
            log.error('Can not find strengthen cost conf. next strengthen level: {0}, item_type:{1}.'.format( next_level, item_type ))
            return NOT_FOUND_CONF, next_cost

        item_conf = get_item_by_itemid(item_id)
        if not item_conf:
            log.error('Can not find item conf. item_id: {0}.'.format( item_id ))
            return NOT_FOUND_CONF, next_cost

        # 判断玩家金币是否充足
        quality   = ITEM_STRENGTHEN_COST[item_conf['Quality']]
        next_cost = cost_conf[quality]
        if next_cost > self.user.base_att.golds:
            log.error('User golds not enough. need golds: {0}, cur golds: {1}.'.format( next_cost, self.user.base_att.golds ))
            return CHAR_GOLD_NOT_ENOUGH, next_cost

        return NO_ERROR, next_cost

    @defer.inlineCallbacks
    def strengthen(self, user_equip_id, strengthen_type):
        '''
        @param: strengthen_type-1:普通强化 2:自动强化
        '''
        res_err = UNKNOWN_ERROR

        attrib = yield self.get( user_equip_id )
        if not attrib:
            log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
            defer.returnValue( res_err )

        _next_level = attrib.level + 1
        res_err, _next_cost  = self.get_cost_by_level_type(_next_level, attrib.item_id, attrib.item_type)
        if res_err:
            defer.returnValue( res_err )

        # 计算暴击等级
        _crit_conf = get_equip_crit_conf(self.user.base_att.vip_level)
        if not _crit_conf:
            log.error('Can not find equip crit conf. user vip_level: {0}.'.format( self.user.base_att.vip_level ))
            defer.returnValue( NOT_FOUND_CONF )

        _pool = []
        for _idx, _weight in enumerate(_crit_conf):
            if _idx and _weight:
                _pool.extend([_idx]*_weight)

        # 自动强化标识符
        _flag = True
        # 强化前的等级, 用于日志记录
        _old_level = attrib.level
        if strengthen_type == STRENGTHEN_AUTO:
            way_type = WAY_EQUIP_STRENGTHEN_AUTO
        else:
            way_type = WAY_EQUIP_STRENGTHEN
        # 策划改进
        _strengthen_count = 0
        _crit_count       = 0
        while _flag:
            # 按权重获取暴击等级, 初始值为1, 默认强化1级
            _crit_level = 1
            if _pool:
                _crit_level = random.choice(_pool)

            _strengthen_count += 1
            if _crit_level > 1:
                _crit_count       += 1
            # 扣金币 升等级
            #self.user.base_att.golds -= _next_cost
            self.user.consume_golds( _next_cost, way_type )
            attrib.strengthen_cost   += _next_cost
            attrib.level             += _crit_level
            _next_level               = attrib.level + 1
            if strengthen_type == STRENGTHEN_NORMAL:
                _flag = False
                break
            res_err, _next_cost  = self.get_cost_by_level_type(_next_level, attrib.item_id, attrib.item_type)
            if res_err:
                _flag = False

        # add syslog
        syslogger(LOG_EQUIP_STRENGTHEN, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_equip_id, attrib.item_id, _old_level, attrib.level, way_type, '')
        # 同步开服七日活动中的任务状态
        self.update_quest_status(OPEN_SERVER_QUEST_ID_6)
        # 已穿戴, 同步camp到redis
        #if attrib.camp_id:
        #    yield self.user.sync_camp_to_redis(update=True)
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_14, _strengthen_count)
        defer.returnValue( (user_equip_id, attrib.item_id, attrib.level, self.user.base_att.golds, _crit_level, _strengthen_count, _crit_count, attrib.strengthen_cost) )

    @defer.inlineCallbacks
    def refine(self, args):
        '''
        @param: refine_type-洗炼方式 1:普通洗炼；2:金币洗炼；3:高级洗炼
                refine_times-单次洗炼的次数 
        '''
        res_err = UNKNOWN_ERROR
        user_equip_id, refine_type, refine_times = args

        attrib = yield self.get( user_equip_id )
        if not attrib:
            log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
            defer.returnValue( res_err )

        # 判断洗炼所需是否满足
        _consume_conf = get_equip_refine_consume( refine_type )
        if not _consume_conf:
            log.error('Can not find the refine type consume conf. refine type: {0}.'.format( refine_type ))
            defer.returnValue( NOT_FOUND_CONF )

        for _consume in _consume_conf:
            _consume_num = _consume['ItemNum']*refine_times
            # 消耗洗炼石
            if (_consume['ItemType'] in BAG_ITEM):
                total_num, item_attribs = yield self.user.bag_item_mgr.get_items( _consume['ItemID'] )
                if _consume_num > total_num:
                    log.error('item id: {0}, need num: {1}, cur num: {2}.'.format( _consume['ItemID'], _consume_num, total_num ))
                    defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            elif ITEM_MONEY_GOLDS == _consume['ItemID']: # 消耗金币
                if _consume_num > self.user.base_att.golds:
                    log.error('User golds not enough. item id: {0}, need item num: {1}.'.format( _consume['ItemID'], _consume_num ))
                    defer.returnValue( CHAR_GOLD_NOT_ENOUGH )
            elif ITEM_MONEY_CREDITS == _consume['ItemID']: # 消耗钻石
                if _consume_num > self.user.base_att.credits:
                    log.error('User credits not enough. item id: {0}, need item num: {1}.'.format( _consume['ItemID'], _consume_num ))
                    defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        # 扣除道具
        items_return = []
        for _consume in _consume_conf:
            _consume_num = _consume['ItemNum']*refine_times
            # 消耗洗炼石
            if (_consume['ItemType'] in BAG_ITEM):
                res_err, used_attribs = yield self.user.bag_item_mgr.use( _consume['ItemID'], _consume_num )
                if res_err:
                    log.error('Use item error.')
                    defer.returnValue( res_err )
                for _a in used_attribs:
                    items_return.append( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num] )
                # 记录洗炼消耗的洗炼石数量
                attrib.refine_cost += _consume_num
                # add syslog
                syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, 0, _consume['ItemID'], _consume_num, WAY_EQUIP_REFINE)
            # 消耗金币
            elif ITEM_MONEY_GOLDS   == _consume['ItemID']: 
                #self.user.base_att.golds       -= _consume_num
                self.user.consume_golds( _consume_num, WAY_EQUIP_REFINE )
            # 消耗钻石
            elif ITEM_MONEY_CREDITS == _consume['ItemID']: 
                #self.user.base_att.credits     -= _consume_num
                yield self.user.consume_credits( _consume_num, WAY_EQUIP_REFINE )

        # 洗炼后的属性值
        _all_levels   = get_equip_refine_levels(attrib.item_id)
        _level        = get_previous_value(attrib.level, _all_levels)
        _refine_conf  = get_equip_refine_conf(attrib.item_id, _level)
        # json格式转为列表
        _old_attribute = loads(attrib.refine_attribute) 
        _old_ids       = {_a[0]:_a[1] for _a in _old_attribute}
        new_attribute  = []
        for _id, _conf in _refine_conf.iteritems():
            _start, _end = _conf[((refine_type-1)*2):(refine_type*2)]
            attr_value   = 0
            for _idx in range(0, refine_times):
                attr_value += random.choice(range(_start, _end))
            _old_value      = _old_ids[_id] if _old_ids.has_key(_id) else 0
            if (_old_value + attr_value) > _conf[-1]:
                attr_value  = _conf[-1] - _old_value
            new_attribute.append( (_id, attr_value, _conf[-1]) )
        #attrib.refine_attribute = dumps( new_attribute )

        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_8, refine_times )
        #成就
        yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_32, refine_times)
        # add syslog
        _all_refine_type = [WAY_UNKNOWN, WAY_EQUIP_REFINE, WAY_EQUIP_REFINE_GOLD, WAY_EQUIP_REFINE_HIGH]
        way_type   = _all_refine_type[refine_type]
        way_others = str(tuple(new_attribute))

        syslogger(LOG_EQUIP_REFINE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_equip_id, attrib.item_id, way_type, refine_times, way_others)

        ## 玩家剩余道具数量
        #total_num, _ = yield self.user.bag_item_mgr.get_items( ITEM_REFINE_STONE )
        defer.returnValue( (user_equip_id, attrib.item_id, new_attribute, items_return, self.user.base_att.golds, self.user.base_att.credits) )
 
    @defer.inlineCallbacks
    def refine_replace(self, user_equip_id, replace_attribute):
        '''
        @summary: 替换洗炼后的属性
        '''
        res_err = UNKNOWN_ERROR
        attrib  = yield self.get( user_equip_id )
        if not attrib:
            log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
            defer.returnValue( res_err )

        # json格式转为列表
        _old_attribute = loads(attrib.refine_attribute) 
        for _attr in replace_attribute:
            if len(_attr) != 3:
                pass
            for _old in _old_attribute:
                if _attr[0] == _old[0]:
                    _old[1] += _attr[1]
                    _old[1] = 0 if _old[1] < 0 else _old[1]
                    break
            else:
                _attr[1] = 0 if _attr[1] < 0 else _attr[1]
                _old_attribute.append( _attr )

        attrib.refine_attribute = dumps( _old_attribute )

        defer.returnValue( (user_equip_id, _old_attribute) )

    @defer.inlineCallbacks
    def equip_replace(self, *args):
        '''
        @summary: 更换某装备
        '''
        camp_id, pos_id, old_ueid, new_ueid = args

        res_err = UNKNOWN_ERROR

        old_attrib  = yield self.get( old_ueid )
        new_attrib  = yield self.get( new_ueid )
        if (not old_attrib) or (not new_attrib):
            log.error('Can not find user equip. old_user_equip_id: {0}, new_user_equip_id: {1}.'.format( old_ueid, new_ueid ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )

        # 检查装备的类型和位置ID是否相符
        if new_attrib.item_type != EQUIP_POSITION_TYPEs.get(pos_id, 0):
            log.error('select equip type error. item type: {0}.'.format( new_attrib.item_type ))
            defer.returnValue( ITEM_TYPE_ERROR )

        # 删除new_ueid对应的旧的阵营信息
        if self.__camp_position.has_key( new_attrib.camp_id )and \
                self.__camp_position[new_attrib.camp_id].has_key( new_attrib.position_id ):
            del self.__camp_position[new_attrib.camp_id][new_attrib.position_id]

        old_attrib.camp_id     = 0
        old_attrib.position_id = 0

        new_attrib.camp_id     = camp_id
        new_attrib.position_id = pos_id

        # 更新 self.__camp_position data
        if not self.__camp_position.has_key( camp_id ):
            self.__camp_position[camp_id] = {}
        self.__camp_position[camp_id][pos_id] = new_ueid

        # 同步开服七日活动中的任务状态
        self.update_quest_status(OPEN_SERVER_QUEST_ID_5)
        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def equip_wear(self, *args):
        '''
        @summary: 穿戴某装备
        '''
        camp_id, pos_id, user_equip_id = args

        res_err = UNKNOWN_ERROR

        attrib  = yield self.get( user_equip_id )
        if not attrib:
            log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )
        
        # 装备已经使用
        #if attrib.camp_id == camp_id:
        #    log.error('Equip wear error. user equip has been on camp. camp id: {0}, position id: {1}.'.format( attrib.camp_id, attrib.position_id ))

        # 检查装备的类型和位置ID是否相符
        if attrib.item_type != EQUIP_POSITION_TYPEs.get(pos_id, 0):
            log.error('select equip type error. item type: {0}.'.format( attrib.item_type ))
            defer.returnValue( ITEM_TYPE_ERROR )

        # 删除equip旧的阵营信息
        if self.__camp_position.has_key( attrib.camp_id )and \
                self.__camp_position[attrib.camp_id].has_key( attrib.position_id ):
            del self.__camp_position[attrib.camp_id][attrib.position_id]

        # 指定camp id 和 position id
        attrib.camp_id     = camp_id
        attrib.position_id = pos_id

        # 更新 self.__camp_position 
        if not self.__camp_position.has_key( camp_id ):
            self.__camp_position[camp_id] = {}
        self.__camp_position[camp_id][pos_id] = user_equip_id

        # 同步开服七日活动中的任务状态
        self.update_quest_status(OPEN_SERVER_QUEST_ID_5)
        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def equip_discard(self, *args):
        '''
        @summary: 卸下某装备
        '''
        camp_id, pos_id, user_equip_id = args

        res_err = UNKNOWN_ERROR

        attrib  = yield self.get( user_equip_id )
        if not attrib:
            log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
            defer.returnValue( res_err )
        #检查装备的camp id 和 position id
        if camp_id != attrib.camp_id or pos_id != attrib.position_id:
            log.error('Equip discard error. equip camp id: {0}, position_id: {1}.'.format( attrib.camp_id, attrib.position_id ))
            defer.returnValue( res_err )

        # 指定camp id 和 position id
        attrib.camp_id     = 0
        attrib.position_id = 0

        # 更新 self.__camp_position
        if self.__camp_position.has_key( camp_id ):
            if self.__camp_position[camp_id].has_key( pos_id ):
                del self.__camp_position[camp_id][pos_id]
        else:
            log.error('Equip camp position data error. __camp_position: {0}.'.format( self.__camp_position ))

        # 同步开服七日活动中的任务状态
        self.update_quest_status(OPEN_SERVER_QUEST_ID_5)
        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def set_one_touch(self, camp_id, args):
        '''
        @summary: 一键装备头盔, 武器, 项链, 护甲
        '''
        if not self.__camp_position.has_key( camp_id ):
            _camp_equip = {}
            self.__camp_position[camp_id] = _camp_equip
        else:
            _camp_equip = self.__camp_position[camp_id]

        for _pos_id, _ueid in enumerate(args):
            if _ueid <= 0:
                continue
            attrib = yield self.get( _ueid )
            if not attrib:
                log.error('Can not find user equip. user_equip_id: {0}.'.format( _ueid ))
                continue

            _pos_id += 2
            # 检查装备的类型和位置ID是否相符
            if attrib.item_type != EQUIP_POSITION_TYPEs.get(_pos_id, 0):
                log.error('select equip type error. item type: {0}, pos_id: {1}.'.format( attrib.item_type, _pos_id ))
                defer.returnValue( ITEM_TYPE_ERROR )
            if _camp_equip.has_key( _pos_id ):
                if _camp_equip[_pos_id] > 0:
                    old_attrib = yield self.get( _camp_equip[_pos_id] )
                    # 新旧装备ID相同
                    if not old_attrib or old_attrib.attrib_id == _ueid:
                        continue
                    old_attrib.camp_id     = 0
                    old_attrib.position_id = 0

            # 指定camp id 和 position id
            attrib.camp_id       = camp_id
            attrib.position_id   = _pos_id
            # 更新 self.__camp_position
            _camp_equip[_pos_id] = _ueid

        # 同步开服七日活动中的任务状态
        self.update_quest_status(OPEN_SERVER_QUEST_ID_5)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def get_camp_equip(self, camp_id):
        '''
        @summary: 获取camp_id的position_id对应的equip
        '''
        yield self._load()
        _camp_equip = [[], [], [], []]

        if not self.__camp_position.has_key(camp_id):
            defer.returnValue( _camp_equip )

        positions = self.__camp_position[camp_id]

        # 2-头盔 3-武器, 4-项链, 5-护甲
        for _pos in range(2, 6):
            if not positions.has_key(_pos):
                continue
            user_equip_id = positions[_pos]

            attrib  = yield self.get( user_equip_id )
            if not attrib:
                log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
                positions[_pos] = 0
                continue
            _camp_equip[_pos-2] = [user_equip_id, attrib.item_id, attrib.level, loads(attrib.refine_attribute)]

        defer.returnValue( _camp_equip )

    @defer.inlineCallbacks
    def gm_get_camp_equip(self, camp_id):
        ''' GM获取阵容中的装备详情 
        '''
        yield self._load()

        dict_data = [{}, {}, {}, {}]
        if not self.__camp_position.has_key(camp_id):
            defer.returnValue( dict_data )
        positions = self.__camp_position[camp_id]

        # 2-头盔 3-武器, 4-项链, 5-护甲
        for _pos in range(2, 6):
            if not positions.has_key(_pos):
                continue

            user_equip_id = positions[_pos]
            attrib  = yield self.get( user_equip_id )
            if not attrib:
                log.error('Can not find user equip. user_equip_id: {0}.'.format( user_equip_id ))
                continue
            refine_attribute = [dict(zip(('attribute_id', 'attribute_value'), _refine)) for _refine in loads(attrib.refine_attribute)]
            dict_data[_pos-2] = {'user_item_id':user_equip_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'level':attrib.level, 'refine':refine_attribute}

        defer.returnValue( dict_data )

    def reborn(self, user_equip_id):
        '''
        @summary: 装备重生后, 所有属性都回到初值
        '''
        equip = yield self.get( user_equip_id )
        if equip:
            equip.strengthen_cost, equip.refine_cost, equip.level = 0, 0, 0
            equip.refine_attribute = dumps( [] )

    @defer.inlineCallbacks
    def gm_equip_info(self):
        yield self._load()
        _equip_info = []
        for attrib in self.__gsattribs.itervalues():
            refine_attribute = [dict(zip(('attribute_id', 'attribute_value'), _refine)) for _refine in loads(attrib.refine_attribute)]
            _equip_info.append( {'user_item_id':attrib.attrib_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'item_cnt':attrib.item_num, 'level':attrib.level, 'refine':refine_attribute, 'exp':0, 'refine_level':0} )

        defer.returnValue( _equip_info )

    @defer.inlineCallbacks
    def update_quest_status(self, quest_type):
        # 检查开服七日活动是否有效
        
        quest_conf = get_open_server_quest_conf(quest_type)
        if not quest_conf:
            defer.returnValue( OPEN_SERVER_IS_CLOSED )

        target_value = []
        had_count = {}
        for i in quest_conf.values():
            target_value.append(i[0])
            had_count[i[0]] = 0
        target_value.sort()
        for value in target_value:
            for gsattrib in self.__gsattribs.itervalues():
            # 获取阵容中的装备信息
                if gsattrib.camp_id <= 0:
                    continue
                if quest_type == OPEN_SERVER_QUEST_ID_5:
                    ctype = ACHIEVEMENT_QUEST_ID_5
                    item_conf = get_item_by_itemid( gsattrib.item_id )
                    if not item_conf:
                        continue
                    if item_conf['Quality'] >= value:
                        had_count[value] += 1
                elif quest_type == OPEN_SERVER_QUEST_ID_6:
                    ctype = ACHIEVEMENT_QUEST_ID_6
                    if gsattrib.level >= value:
                        had_count[value] += 1
        # 同步开服七日活动中的任务状态
        yield self.user.open_server_mgr.update_open_server_activity_quest( quest_type, had_count)
#        yield self.user.achievement_mgr.update_achievement_status(ctype, had_count)
  


