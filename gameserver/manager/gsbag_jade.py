#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

import random

from time     import time
from log      import log
from errorno  import *
from constant import *
from utils    import rand_num
from redis    import redis
from system   import get_jade_level_conf, get_jade_cost_conf, get_item_by_itemid, \
        get_jade_strengthen_conf

from twisted.internet       import defer
from manager.gsattribute    import GSAttribute
from models.randpackage     import package_open
from models.item            import ITEM_MODELs
from protocol_manager       import gw_broadcast
from syslogger              import syslogger


class GSBagJadeMgr(object):
    '''
    @summary: 玩家玉魄背包
    @param  : camp_id范围1-6,
    @param  : position_id范围2-7, 编号对应阵容位置依次为从左到右,从上到下。
    '''
    _table = 'bag_jade'

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        self.__gsattribs = None

        self.__loading = False
        self.__defers  = []
        # 鉴玉当前等级
        self.random_jade_level = 1

    @defer.inlineCallbacks
    def _load(self):
        if self.__gsattribs is None:
            if not self.__loading:
                self.__loading = True
                self.__gsattribs = yield GSAttribute.load( self.cid, GSBagJadeMgr._table )
                for gsattrib in self.__gsattribs.itervalues():
                    # 获取阵容中的玉魄信息
                    if gsattrib.camp_id > 0:
                        # 异常数据
                        if gsattrib.position_id < 1:
                            gsattrib.camp_id = 0

                # 获取鉴玉当前等级
                _level = yield redis.hget(HASH_RANDOM_JADE_LEVEL, self.cid)
                self.random_jade_level = int(_level) if _level else 1

                for d in self.__defers:
                    d.callback(True)

                self.__loading = False
                self.__defers  = []
            else:
                d = defer.Deferred()
                self.__defers.append(d)
                yield d

    def sync_to_cs(self):
        if self.__gsattribs:
            for attrib in self.__gsattribs.itervalues():
                attrib.syncToCS()

    @defer.inlineCallbacks
    def get(self, user_item_id):
        yield self._load()
        defer.returnValue( self.__gsattribs.get(user_item_id, None) )

    @defer.inlineCallbacks
    def cur_capacity(self):
        yield self._load()
        count = 0
        # 已穿戴的玉魄不计算在玉魄背包内
        for attrib in self.__gsattribs.itervalues():
            if attrib.camp_id == 0:
                count += 1
        defer.returnValue( count )

    @defer.inlineCallbacks
    def value_list(self, index):
        yield self._load()
        count = 0
        value_list = []
        for attrib in self.__gsattribs.itervalues():
            value_list.append( (attrib.attrib_id, attrib.item_id, attrib.level, attrib.exp, attrib.camp_id) )
            # 已穿戴的玉魄不计算在玉魄背包内
            if attrib.camp_id == 0:
                count += 1

        defer.returnValue( (count, value_list[index:index+JADE_PER_PAGE]) )

    @defer.inlineCallbacks
    def new(self, item_id, item_num, way_type=WAY_UNKNOWN, way_others=''):
        yield self._load()
        item_conf = get_item_by_itemid( item_id )
        if not item_conf:
            log.error('Can not find conf. cid: {0}, item_id: {1}.'.format( self.cid, item_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )
        # 检查道具类型
        item_type  = item_conf['ItemType']
        if item_type not in BAG_JADE:
            log.error('new. Item type error. cid: {0}, item_id: {1}.'.format( self.cid, item_id ))
            defer.returnValue( (ITEM_TYPE_ERROR, None) )

        time_now  = int(time())
        new_items = []

        while item_num >= 1:
            res_err, new_attrib = yield self.create_table_data(item_type, item_id, 1, time_now)
            if res_err:
                defer.returnValue( (UNKNOWN_ERROR, None) )
            item_num -= 1
            new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, 1], new_items )

        # add syslog
        for _item in new_items:
            syslogger(LOG_ITEM_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _item[0], _item[2], _item[3], way_type, way_others)
        defer.returnValue( (NO_ERROR, new_items) )

    @defer.inlineCallbacks
    def create_table_data(self, item_type, item_id, item_num, time_now, camp_id=0, position_id=0, level=0, exp=0):
        gsattrib = GSAttribute( self.cid, GSBagJadeMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, item_type=item_type, item_id=item_id, item_num=item_num, camp_id=camp_id, position_id=position_id, level=level, exp=exp, deleted=0, create_time=time_now, update_time=time_now, del_time=0 )
        if res_err:
            log.error('GSBagJadeMgr create table data error. ')
            defer.returnValue( (res_err, None) )

        self.__gsattribs[gsattrib.attrib_id] = gsattrib
        defer.returnValue( (NO_ERROR, gsattrib) )

    def delete_table_data(self, attrib_id):
        if self.__gsattribs.has_key( attrib_id ):
            gsattrib = self.__gsattribs[attrib_id]
            gsattrib.delete()
            del self.__gsattribs[attrib_id]
        else:
            log.error('Can not find delete data. cid: {0}, attrib_id: {1}.'.format( self.cid, attrib_id ))

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
    def random_new_jade(self, random_times):
        ''' 获取新的玉魄 '''
        # 检查等级限制条件
        if random_times == JADE_RANDOM_TIMES_TEN:
            if (self.user.level < JADE_RANDOM_TEN_LEVEL) and (self.user.vip_level < JADE_RANDOM_TEN_VIP_LEVEL):
                defer.returnValue( JADE_RANDOM_TEN_ERROR )

        # 鉴玉
        new_jades, new_items = [], []
        msg_item_ids = [] # 需要走马灯通告的道具信息

        _curr_random_level = self.random_jade_level
        _golds_cost, _credits_cost, _left_golds, _left_credits = 0, 0, self.user.golds, self.user.credits

        for _idx in range(0, random_times):
            cost_conf = get_jade_cost_conf( _curr_random_level )
            # 检查消耗数量限制
            if not cost_conf:
                defer.returnValue( NOT_FOUND_CONF )
            if ITEM_TYPE_MONEY != cost_conf['CostItemType']:
                defer.returnValue( UNKNOWN_ITEM_ERROR )
            if ITEM_MONEY_GOLDS == cost_conf['CostItemID']:
                if _left_golds < cost_conf['CostItemNum']:
                    defer.returnValue( CHAR_GOLD_NOT_ENOUGH )
                _left_golds -= cost_conf['CostItemNum']
                _golds_cost += cost_conf['CostItemNum']
            elif ITEM_MONEY_CREDITS == cost_conf['CostItemID']:
                if _left_credits < cost_conf['CostItemNum']:
                    defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
                _left_credits -= cost_conf['CostItemNum']
                _credits_cost += cost_conf['CostItemNum']
            else:
                defer.returnValue( UNKNOWN_ITEM_ERROR )

            _chest_id  = JADE_RANDOM_POOLS[_curr_random_level]
            _item_rand = yield package_open(self.user, _chest_id)
            if not _item_rand:
                defer.returnValue( NOT_FOUND_CONF )

            new_jades.append( _item_rand[:3] )
            if _item_rand[3]:
                msg_item_ids.append( _item_rand[:3] )

            # 鉴玉等级会有一定几率提示、不变、回到初始等级, 并有一定概率获得额外的道具
            _next_level, _extra_item = self.random_next_level(_curr_random_level)
            if _next_level != _curr_random_level:
                _curr_random_level = _next_level
                yield redis.hset(HASH_RANDOM_JADE_LEVEL, self.cid, _next_level)
            if _extra_item:
                new_items.append( _extra_item )
        # 扣金币或钻石
        if _golds_cost:
            self.user.consume_golds( _golds_cost, WAY_JADE_RANDOM )
        if _credits_cost:
            yield self.user.consume_credits( _credits_cost, WAY_JADE_RANDOM )
        # 更新最新等级
        self.random_jade_level = _curr_random_level

        #log.info('For Test. _golds_cost: {0}, _credits_cost: {1}, new_jades: {2}, new_items: {3}.'.format( _golds_cost, _credits_cost, new_jades, new_items ))
        add_jades, add_items = [], []
        q = 0
        for _type, _id, _num in new_jades:
            _model = ITEM_MODELs.get(_type, None)
            if not _model:
                log.error('Unknown item type. cid: {0}, ItemType: {1}.'.format( self.cid, _type ))
                continue
            res_err, value = yield _model(self.user, ItemID=_id, ItemNum=_num, CapacityFlag=False, AddType=WAY_JADE_RANDOM)
            _quality = get_item_by_itemid(_id).get('Quality', 0)
            if _quality >= 2:
            #品质大于2，开服狂欢
                q+= 1
            if not res_err and value:
                add_jades.extend( value )
            else:
                log.warn('User add items error. cid: {0}, res_err: {1}, value: {2}.'.format( self.cid, res_err, value ))
        # 开服狂欢
        yield self.user.open_server_mgr.update_open_server_activity_quest(OPEN_SERVER_QUEST_ID_16, q)
        yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_16, q)
        # 新增额外掉落的道具
        for _type, _id, _num in new_items:
            _model = ITEM_MODELs.get(_type, None)
            if not _model:
                log.error('Unknown item type. cid: {0}, ItemType: {1}.'.format( self.cid, _type ))
                continue
            res_err, value = yield _model(self.user, ItemID=_id, ItemNum=_num, CapacityFlag=False, AddType=WAY_JADE_RANDOM)
            if not res_err and value:
                add_items.extend( value )
            else:
                log.warn('User add items error. cid: {0}, res_err: {1}, value: {2}.'.format( self.cid, res_err, value ))
        if msg_item_ids:
            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_RARE_ITEM, [self.user.nick_name, _chest_id, msg_item_ids]]]
            gw_broadcast('sync_broadcast', [message])

        defer.returnValue( (self.user.golds, self.user.credits, _curr_random_level, add_jades, add_items) )

    def random_next_level(self, curr_level):
        ''' 鉴玉等级会有一定几率提示、不变、回到初始等级 '''
        #log.info('For Test. before level: {0}.'.format( curr_level ))
        level_conf = get_jade_level_conf(curr_level)
        if not level_conf:
            return curr_level, []

        total_rate = 0
        for _v in level_conf.itervalues():
            total_rate += _v['Rate']

        if total_rate <= 0:
            log.warn('There is no level pool. cid: {0}, curr_level: {1}.'.format( self.cid, curr_level ))
            return curr_level, extra_item

        curr_int = 0
        randint  = rand_num(total_rate)

        extra_item = []
        for _v in level_conf.itervalues():
            if randint < (curr_int + _v['Rate']):
                curr_level = _v['TargetLevel']
                #log.error('For Test. curr_level: {0}, randint: {1}, curr_int: {2}, _rate: {3}, total_rate: {4}.'.format( curr_level, randint, curr_int, _v['Rate'], total_rate ))
                break
            else:
                curr_int += _v['Rate']
        else:
            curr_level = curr_level

        rand_int   = random.randint(0, 10000)
        if rand_int <= level_conf[curr_level]['ExtraOdds']:
            extra_item = [level_conf[curr_level]['ItemType'], level_conf[curr_level]['ItemID'], level_conf[curr_level]['ItemNum']]

        #log.info('For Test. after level: {0}, extra_item: {1}, total_rate: {2}.'.format( curr_level, extra_item, total_rate ))
        return curr_level, extra_item

    @defer.inlineCallbacks
    def upgrade_random_level(self):
        ''' 将当前鉴玉等级提升到特定等级(暂定4级宝玉) '''
        items_return = []
        total_num, item_attribs = yield self.user.bag_item_mgr.get_items( ITEM_JADE_UPGRADE_ID )
        if total_num > 0:
            res_err, used_attribs = yield self.user.bag_item_mgr.use( ITEM_JADE_UPGRADE_ID, 1 )
            if res_err:
                defer.returnValue( res_err )
            else:
                self.random_jade_level = JADE_UPGRADE_LEVEL
                yield redis.hset(HASH_RANDOM_JADE_LEVEL, self.cid, JADE_UPGRADE_LEVEL)
                # used_attribs-已使用的道具
                for _a in used_attribs:
                    items_return.append( [_a.attrib_id, ITEM_TYPE_ITEM, ITEM_JADE_UPGRADE_ID, _a.item_num] )
                    # add syslog
                    syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _a.attrib_id, ITEM_JADE_UPGRADE_ID, 1, WAY_JADE_UPGRADE_LEVEL)
        else:
            if JADE_UPGRADE_LEVEL_CREDITS > self.user.credits:
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            else:
                self.random_jade_level = JADE_UPGRADE_LEVEL
                yield redis.hset(HASH_RANDOM_JADE_LEVEL, self.cid, JADE_UPGRADE_LEVEL)
                yield self.user.consume_credits( JADE_UPGRADE_LEVEL_CREDITS, WAY_JADE_UPGRADE_LEVEL )

        item_rand = yield package_open(self.user, JADE_UPGRADE_CHEST_ID)
        if not item_rand:
            defer.returnValue( NOT_FOUND_CONF )
        add_item = []
        _model   = ITEM_MODELs.get(item_rand[0], None)
        if _model:
            res_err, value = yield _model(self.user, ItemID=item_rand[1], ItemNum=item_rand[2], AddType=WAY_JADE_UPGRADE_LEVEL)
            if not res_err and value:
                add_item = value[0]
        if not add_item:
            defer.returnValue( UNKNOWN_ERROR )

        defer.returnValue( (self.user.credits, self.random_jade_level, items_return, add_item) )

    @defer.inlineCallbacks
    def strengthen(self, user_jade_id, jades_data):
        '''
        @summary: 消耗jades_data强化user_jade_id
        '''
        attrib = yield self.get(user_jade_id)
        if not attrib:
            defer.returnValue( UNKNOWN_JADE_ERROR )

        # 道具配置
        item_conf = get_item_by_itemid(attrib.item_id)
        if not item_conf:
            defer.returnValue( NOT_FOUND_CONF )

        # 要强化的道具品质、经验、强化等级
        _total_exp = attrib.exp
        _cur_level = attrib.level
        quality    = JADE_STRENGTHEN_EXP[item_conf['Quality']]

        # 获取消耗的jades_data可获得的经验值
        for _ujid in jades_data:
            use_attrib = yield self.get( _ujid )
            if not use_attrib:
                defer.returnValue( res_err )
            # 道具配置
            use_item_conf = get_item_by_itemid(use_attrib.item_id)
            if not use_item_conf:
                log.error('Can not find item conf. cid: {0}, item_id: {0}.'.format( self.cid, attrib.item_id ))
                defer.returnValue( CLIENT_DATA_ERROR )
            # 类型不匹配/已穿戴的不可用于升级
            if (use_attrib.item_type != attrib.item_type) \
               or (use_attrib.camp_id > 0):
                log.error('Item in camp error. cid: {0}, item_id: {1}, item type: {2}, camp_id: {3}.'.format( \
                    self.cid, use_attrib.item_id, (attrib.item_type, use_attrib.item_type), use_attrib.camp_id))
                defer.returnValue( CLIENT_DATA_ERROR )

            _attributs = use_item_conf['attributes']
            for _attr in _attributs:
                if _attr['AttributeID'] == ATTRIBUTE_TYPE_JADE_EXP:
                    _total_exp += _attr['Value']
            # 计算升级获得的经验, 玉魄初始等级为0
            use_quality = JADE_STRENGTHEN_EXP[use_item_conf['Quality']]
            for _level in range(1, use_attrib.level+1):
                use_exp_conf = get_jade_strengthen_conf( _level )
                had_got_exp = use_exp_conf.get(use_quality, 0)
                if had_got_exp:
                    _total_exp += had_got_exp

        # 强化前的等级
        _old_level = attrib.level
        # 删除用于强化的宝物
        for _ujid in jades_data:
            self.delete_table_data( _ujid )

        _max_level = (self.user.level / 10 ) * 5
        while _total_exp > 0:
            # 玉魄等级有限制
            if _cur_level >= _max_level:
                break
            # 强化宝物所需exp配置
            exp_conf  = get_jade_strengthen_conf( _cur_level+1 )
            if not exp_conf:
                log.error('Can not find strengthen exp conf. strengthen next level: {0}.'.format( _cur_level+1 ))
                break

            need_exp    = exp_conf[quality]
            # 经验不足以升级
            if (_total_exp - need_exp) < 0:
                break
            _total_exp -= need_exp
            _cur_level += 1

        attrib.level = _cur_level
        attrib.exp   = _total_exp

        ## add syslog
        #way_others = str(tuple(treasures_data))
        #syslogger(LOG_JADE_STRENGTHEN, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_treasure_id, attrib.item_id, _old_level, attrib.level, way_others)

        defer.returnValue( (user_jade_id, attrib.item_id, _cur_level, _total_exp) )

    @defer.inlineCallbacks
    def get_camp_positions(self, camp_id):
        '''
        @summary: 获取某一阵营中所有位置上的玉魄
        '''
        yield self._load()
        positions = {}
        for gsattrib in self.__gsattribs.itervalues():
            # 获取阵容中的玉魄信息
            if gsattrib.camp_id != camp_id:
                continue
            had_gsattrib = positions.get(gsattrib.position_id, None)
            if had_gsattrib:
                had_gsattrib.camp_id     = 0
                had_gsattrib.position_id = 0
                log.error('Had more than one jade in position_id<{0}>, cid: {1}.'.format( gsattrib.position_id, self.cid ))
            positions[gsattrib.position_id] = gsattrib

        defer.returnValue( positions )

    @defer.inlineCallbacks
    def get_camp_jade(self, camp_id):
        '''
        @summary: 获取camp_id的position_id对应的jade
        '''
        positions = yield self.get_camp_positions(camp_id)
        if not positions:
            defer.returnValue( [] )

        camp_jades = [camp_id]
        for _pos in range(1, 9):
            if not positions.has_key(_pos):
                camp_jades.append( [] )
                continue
            attrib = positions[_pos]
            camp_jades.append( [attrib.attrib_id, attrib.item_id, attrib.level] )
 
        defer.returnValue( camp_jades )

    @defer.inlineCallbacks
    def jade_replace(self, *args):
        '''
        @summary: 更换某玉魄
        '''
        camp_id, pos_id, old_ujid, new_ujid = args

        new_attrib = yield self.get( new_ujid )
        if not new_attrib:
            defer.returnValue( UNKNOWN_JADE_ERROR )

        positions = yield self.get_camp_positions(camp_id)
        pos_old_attrib = positions.get(pos_id, None)
        if pos_old_attrib:
            pos_old_attrib.camp_id     = 0
            pos_old_attrib.position_id = 0
            if pos_old_attrib.attrib_id != old_ujid:
                log.error('old_ujid not match. cid: {0}, args: {1}.'.format( self.cid, args ))

        new_attrib.camp_id     = camp_id
        new_attrib.position_id = pos_id

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def jade_wear(self, *args):
        '''
        @summary: 穿戴某玉魄
        '''
        camp_id, pos_id, user_jade_id = args

        attrib = yield self.get( user_jade_id )
        if not attrib:
            defer.returnValue( UNKNOWN_JADE_ERROR )

        positions = yield self.get_camp_positions(camp_id)
        pos_old_attrib = positions.get(pos_id, None)
        if pos_old_attrib:
            pos_old_attrib.camp_id     = 0
            pos_old_attrib.position_id = 0

        attrib.camp_id     = camp_id
        attrib.position_id = pos_id

        defer.returnValue( NO_ERROR )
 
    @defer.inlineCallbacks
    def set_one_touch(self, *args):
        '''
        @summary: 一键装备玉魄
        '''
        camp_id, one_touch_data = args

        positions = yield self.get_camp_positions(camp_id)

        for pos_id, new_ujid in enumerate(one_touch_data):
            if new_ujid <= 0:
                continue
            attrib = yield self.get( new_ujid )
            if not attrib:
                log.error('Unknown jade error. cid: {0}, new_ujid: {1}.'.format( self.cid, new_ujid ))
                continue
            pos_id += 1
            # 处理该pos_id上的旧的玉魄
            pos_old_attrib = positions.get(pos_id, None)
            if pos_old_attrib:
                pos_old_attrib.camp_id     = 0
                pos_old_attrib.position_id = 0
 
            attrib.camp_id     = camp_id
            attrib.position_id = pos_id

        defer.returnValue( NO_ERROR )


