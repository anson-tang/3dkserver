#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time     import time
from log      import log
from errorno  import *
from constant import *
from utils    import split_items, datetime2string

from syslogger              import syslogger
from twisted.internet       import defer
from system                 import get_item_by_itemid, get_treasure_exp_conf, get_treasure_refine_conf
from manager.gsattribute    import GSAttribute

TREASURE_POSITION_TYPEs = {6: ITEM_TYPE_BOOKWAR, 7: ITEM_TYPE_HORSE}

class GSBagTreasureMgr(object):
    '''
    @summary: 玩家宝物背包
    @param  : camp_id范围1-6, 
    @param  : position_id范围6-7, 6-兵书, 7-战马
    @param  : item_num默认为 1
    '''
    _table  = 'bag_treasure'

    def __init__(self, user):
        '''
        @param: __camp_position format: {camp_id: {position_id: user_treasure_id, ...}, ...}, 其中camp_id范围1-6, position_id范围是1-4
        '''
        self.user = user
        self.cid  = user.cid
        self.__gsattribs = None
        # 宝物在阵容中的信息 在阵容中新增、替换、卸下宝物时需要同时维护
        self.__camp_position = {}

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def _load(self):
        if self.__gsattribs is None:
            if not self.__loading:
                self.__loading = True
                self.__gsattribs = yield GSAttribute.load( self.cid, GSBagTreasureMgr._table )

                # 获取阵容中的宝物信息
                for gsattrib in self.__gsattribs.itervalues():
                    if gsattrib.camp_id > 0:
                        if self.__camp_position.has_key( gsattrib.camp_id ):
                            _camp_treasure = self.__camp_position[gsattrib.camp_id]
                        else:
                            _camp_treasure = {}
                            self.__camp_position[gsattrib.camp_id] = _camp_treasure
                        if not _camp_treasure.has_key(gsattrib.position_id):
                            _camp_treasure[gsattrib.position_id] = gsattrib.attrib_id

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
    def get_item_by_item_id(self, item_id):
        ''' __gsattribs中保存是按照规则排序后的数据
        '''
        yield self._load()
        for attrib in self.__gsattribs.itervalues():
            if attrib.item_id == item_id:
                defer.returnValue( attrib )
        defer.returnValue( None )

    @defer.inlineCallbacks
    def get_item_to_refine(self, user_treasure_id, item_id):
        ''' 从背包中获取能用于精炼的道具, 初始道具可用, 即未装备/未强化/未精炼
        '''
        yield self._load()
        valid_attribs = []
        for attrib in self.__gsattribs.itervalues():
            # 排除自己
            if user_treasure_id == attrib.attrib_id:
                continue
            # 添加限制
            if attrib.item_id == item_id and (attrib.camp_id == 0) and (attrib.level == 0) and (attrib.refine_level == 0):
                valid_attribs.append( attrib )
        defer.returnValue( valid_attribs )

    @defer.inlineCallbacks
    def get(self, user_item_id):
        yield self._load()
        defer.returnValue( self.__gsattribs.get(user_item_id, None) )

    @defer.inlineCallbacks
    def cur_capacity(self):
        yield self._load()
        count = 0
        # 已穿戴的宝物不计算在宝物背包内
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
            value_list.append( (attrib.attrib_id, attrib.item_id, attrib.level, attrib.exp, attrib.refine_level, attrib.camp_id) )
            # 已穿戴的宝物不计算在宝物背包内
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
        if item_type not in BAG_TREASURE:
            log.error('new. Item type error. item_id: {0}.'.format( item_id ))
            defer.returnValue( (ITEM_TYPE_ERROR, None) )
        # 判断图鉴
        yield self.user.atlaslist_mgr.new_atlaslist(CATEGORY_TYPE_TREASURE, item_type, item_conf['Quality'], item_id)

        time_now   = int(time()) #datetime2string()
        MAX_NUM    = item_conf['MaxOverlyingCount'] or (2 ** 16 - 1)
        new_items  = []
        for attrib in self.__gsattribs.itervalues():
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
    def create_table_data(self, item_type, item_id, item_num, time_now, level=0, exp=0, refine_level=0, camp_id=0, position_id=0):
        gsattrib = GSAttribute( self.cid, GSBagTreasureMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, item_type=item_type, item_id=item_id, item_num=item_num, camp_id=camp_id, position_id=position_id, level=level, exp=exp, refine_level=refine_level, deleted=0, create_time=time_now, update_time=time_now, del_time=0, aux_data='' )
        if res_err:
            log.error('GSBagTreasureMgr create table data error. ')
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

    def exp_to_treasure(self, horse_exp, bookwar_exp):
        '''
        @summary: 用宝物的经验计算可兑换成经验马或经验书的个数
        '''
        basic_exp, horse_num, bookwar_num, gold_horse_num, gold_bookwar_num = 0, 0, 0, 0, 0
        # 经验马
        horse_conf = get_item_by_itemid( EXP_HORSE_ID )
        if horse_conf and (horse_exp > 0):
            for _attr in horse_conf['attributes']:
                if _attr['AttributeID'] == ATTRIBUTE_TYPE_HORSE_EXP:
                    basic_exp += _attr['Value']
                    break
            # 计算可折算的经验马个数
            if basic_exp > 0:
                horse_num = (horse_exp / basic_exp)
                gold_horse_num = horse_num / 5
                horse_num = horse_num % 5
        # 经验书
        basic_exp    = 0
        bookwar_conf = get_item_by_itemid( EXP_BOOKWAR_ID )
        if bookwar_conf and (bookwar_exp > 0):
            for _attr in bookwar_conf['attributes']:
                if _attr['AttributeID'] == ATTRIBUTE_TYPE_BOOKWAR_EXP:
                    basic_exp += _attr['Value']
                    break
            # 计算可折算的经验马个数
            if basic_exp > 0:
                bookwar_num = (bookwar_exp / basic_exp)
                gold_bookwar_num = bookwar_num / 5
                bookwar_num = bookwar_num % 5

        return horse_num, bookwar_num, gold_horse_num, gold_bookwar_num

    @defer.inlineCallbacks
    def add_exp_treasure(self, item_type, total_exp):
        ''' 用经验值兑换经验马或经验书 '''
        res_err, res_value = NO_ERROR, []

        if item_type == ITEM_TYPE_BOOKWAR:
            horse_num, bookwar_num, gold_horse_num, gold_bookwar_num = self.exp_to_treasure( 0, total_exp )
        elif item_type == ITEM_TYPE_HORSE:
            horse_num, bookwar_num, gold_horse_num, gold_bookwar_num = self.exp_to_treasure( total_exp, 0 )
        else:
            log.error('Unknown item type. item_type: {0}.'.format( item_type ))
            defer.returnValue( UNKNOWN_ITEM_ERROR, [] )

        if horse_num > 0:
            res_err, res_value = yield self.new( EXP_HORSE_ID, horse_num )
        elif bookwar_num > 0:
            res_err, res_value = yield self.new( EXP_BOOKWAR_ID, bookwar_num )

        if gold_horse_num > 0:
            _err, _value = yield self.new( EXP_GOLD_HORSE_ID, gold_horse_num )
            if not _err:
                res_value.extend( _value )
        elif gold_bookwar_num > 0:
            _err, _value = yield self.new( EXP_GOLD_BOOKWAR_ID, gold_bookwar_num )
            if not _err:
                res_value.extend( _value )

        defer.returnValue( (res_err, res_value) )

    @defer.inlineCallbacks
    def get_sell_back_cost(self, *args):
        '''
        @summary: 出售道具时返还消耗的金币
        '''
        user_item_ids, = args

        res_err = [UNKNOWN_TREASURE_ERROR, 0]
        for _utid in user_item_ids:
            attrib  = yield self.get( _utid )
            if not attrib:
                defer.returnValue( res_err )

            item_conf = get_item_by_itemid( attrib.item_id )
            if not item_conf:
                defer.returnValue( res_err )
            if not item_conf['Price']:
                res_err[0] = ITEM_CANNOT_SELL
                defer.returnValue( res_err )

            res_err[1] += item_conf['Price'] * attrib.item_num

            quality = ITEM_STRENGTHEN_COST[item_conf['Quality']]
            had_exp = attrib.exp
            for _level in range(1, attrib.level+1):
                exp_conf = get_treasure_exp_conf( _level )
                if not exp_conf:
                    continue
                had_exp += exp_conf.get(quality, 0)
            res_err[1] += had_exp * TREASURE_STRENGTHEN_EXP_TO_GOLDS
            #log.error('For Test. _utid: {0}, cost: {1}, Price: {2}.'.format( _utid, had_exp * TREASURE_STRENGTHEN_EXP_TO_GOLDS, item_conf['Price'] ))

        for _utid in user_item_ids:
            self.delete_table_data(_utid)

        res_err[0] = NO_ERROR
        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def strengthen(self, user_treasure_id, treasures_data):
        '''
        @summary: 消耗treasures_data强化user_treasure_id
        '''
        res_err = UNKNOWN_TREASURE_ERROR

        attrib = yield self.get( user_treasure_id )
        if not attrib:
            log.error('Can not find user treasure. user_treasure_id: {0}.'.format( user_treasure_id ))
            defer.returnValue( res_err )

        # 道具配置
        item_conf = get_item_by_itemid(attrib.item_id)
        if not item_conf:
            log.error('Can not find item conf. item_id: {0}.'.format( attrib.item_id ))
            defer.returnValue( NOT_FOUND_CONF )
        # 要强化的道具品质、经验、强化等级
        quality    = ITEM_STRENGTHEN_COST[item_conf['Quality']]
        _total_exp = 0
        _cur_level = attrib.level

        # 获取消耗的treasures_data可获得的经验值
        for _utid in treasures_data:
            use_attrib = yield self.get( _utid )
            if not use_attrib:
                log.error('Can not find user treasure. user_treasure_id: {0}.'.format( _utid ))
                defer.returnValue( res_err )
            # 道具配置
            item_conf = get_item_by_itemid(use_attrib.item_id)
            if not item_conf:
                log.error('Can not find item conf. item_id: {0}.'.format( attrib.item_id ))
                defer.returnValue( CLIENT_DATA_ERROR )
            # 类型不匹配/已装备的不可用于强化
            if (use_attrib.item_type != attrib.item_type) \
               or (use_attrib.camp_id > 0):
                log.error('Item type not match or in camp. item_id: {0}, item type: {1}, camp_id: {2}.'.format( \
                    use_attrib.item_id, (attrib.item_type, use_attrib.item_type), use_attrib.camp_id))
                defer.returnValue( CLIENT_DATA_ERROR )

            _attributs = item_conf['attributes']
            for _attr in _attributs:
                if _attr['AttributeID'] in (ATTRIBUTE_TYPE_HORSE_EXP, ATTRIBUTE_TYPE_BOOKWAR_EXP):
                    _total_exp += _attr['Value']
            # 计算升级获得的经验, 宝物初始等级为0
            use_quality = ITEM_STRENGTHEN_COST[item_conf['Quality']]
            for _level in range(1, use_attrib.level+1):
                use_exp_conf = get_treasure_exp_conf( _level )
                had_got_exp = use_exp_conf.get(use_quality, 0)
                if had_got_exp:
                    _total_exp += had_got_exp
        # 金币不足
        if _total_exp*TREASURE_STRENGTHEN_EXP_TO_GOLDS > self.user.base_att.golds:
            log.error('user golds not enough. cur_golds: {0}, need_golds: {1}.'.format(self.user.base_att.golds, _total_exp*TREASURE_STRENGTHEN_EXP_TO_GOLDS))
            defer.returnValue( CHAR_GOLD_NOT_ENOUGH )
        # 扣金币
        #self.user.base_att.golds -= _total_exp*TREASURE_STRENGTHEN_EXP_TO_GOLDS 
        self.user.consume_golds( _total_exp*TREASURE_STRENGTHEN_EXP_TO_GOLDS, WAY_TREASURE_STRENGTHEN )

        _total_exp += attrib.exp
        # 强化前的等级
        _old_level = attrib.level
        # 删除用于强化的宝物
        for _utid in treasures_data:
            self.delete_table_data( _utid )

        while _total_exp > 0:
            # 强化宝物所需exp配置
            exp_conf  = get_treasure_exp_conf( _cur_level+1 )
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

        # add syslog
        way_others = str(tuple(treasures_data))
        syslogger(LOG_TREASURE_STRENGTHEN, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_treasure_id, attrib.item_id, _old_level, attrib.level, way_others)
        # 同步camp到redis
        #if attrib.camp_id:
        #    yield self.user.sync_camp_to_redis(update=True)

        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_15, 1)
        defer.returnValue( (user_treasure_id, attrib.item_id, _cur_level, _total_exp, self.user.base_att.golds) )

    @defer.inlineCallbacks
    def refine(self, user_treasure_id):
        '''
        @summary:  只有精炼等级为0, 强化等级为0的宝物才可作消耗材料
              只有品级（QualityLevel）大于7的才可以精炼
        '''
        res_err = UNKNOWN_TREASURE_ERROR

        attrib = yield self.get( user_treasure_id )
        if not attrib:
            log.error('Can not find user treasure. user_treasure_id: {0}.'.format( user_treasure_id ))
            defer.returnValue( res_err )

        refine_conf = get_treasure_refine_conf(attrib.item_id, attrib.refine_level+1)
        if not refine_conf:
            log.error('Can not find refine conf. item_id: {0}, refine level: {1}.'.format( attrib.item_id, attrib.refine_level+1 ))
            defer.returnValue( NOT_FOUND_CONF )
        # 道具配置 自身品级不满足
        item_conf = get_item_by_itemid(attrib.item_id)
        if (not item_conf) or (item_conf['QualityLevel'] <= TREASURE_REFINE_QUALITYLEVEL_MAX):
            log.error('Can not refine treasure. No conf or quality_level limit. item_id: {0}.'.format( attrib.item_id ))
            defer.returnValue( CLIENT_DATA_ERROR )

        # 金币不足
        if refine_conf['CostGold'] > self.user.base_att.golds:
            log.error('user golds not enough. need_golds: {0}, cur_golds: {1}.'.format( refine_conf['CostGold'], self.user.base_att.golds ))
            defer.returnValue( CHAR_GOLD_NOT_ENOUGH )

        # 消耗道具不足, 道具类型格式:道具ID:道具数量
        items_list = split_items( refine_conf['CostItemList'] )
        cost_attribs = [] # 要消耗的宝物
        for _type, _id, _num in items_list:
            if _type in BAG_TREASURE:
                all_attribs = yield self.get_item_to_refine( user_treasure_id, _id )
                if len(all_attribs) < _num:
                    log.error('user item not enough. item_id: {2}, cur_item_num: {0}, need_item_num: {1}.'.format( len(all_attribs), _num, _id ))
                    defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
                cost_attribs.extend( all_attribs[:_num] )
            elif _type == ITEM_TYPE_ITEM:
                total_num, item_attribs = yield self.user.bag_item_mgr.get_items( _id )
                if total_num < _num:
                    log.error('user item not enough. cid:{0}, item_id:{1}, need:{2}, curr:{3}.'.format( self.cid, _id, _num, total_num ))
                    defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            else:
                log.error("Unknown item type. cost item: {0}.".format( refine_conf['CostItemList'] ))
                defer.returnValue( UNKNOWN_ITEM_ERROR )
        # 扣宝物
        items_return = []
        for _attrib in cost_attribs:
            self.delete_table_data( _attrib.attrib_id )
            items_return.append( _attrib.attrib_id )
        # 扣道具
        left_items = []
        for _type, _id, _num in items_list:
            if _type != ITEM_TYPE_ITEM:
                continue
            res_err, used_attribs = yield self.user.bag_item_mgr.use( _id, _num )
            if res_err:
                log.error('Use item error. cid:{0}, _type:{1}, _id:{2}, _num:{3}.'.format( self.cid, _type, _id, _num ))
            # used_attribs-已使用的道具
            for _a in used_attribs:
                left_items.append( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num] )

        # 扣金币
        #self.user.base_att.golds -= refine_conf['CostGold']
        self.user.consume_golds( refine_conf['CostGold'], WAY_TREASURE_REFINE )
        attrib.refine_level += 1

        # add syslog
        way_others = str(tuple(items_return))
        syslogger(LOG_TREASURE_REFINE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_treasure_id, attrib.item_id, attrib.refine_level-1, attrib.refine_level, way_others)

        # 同步camp到redis
        #if attrib.camp_id:
        #    yield self.user.sync_camp_to_redis(update=True)
        yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_33, attrib.refine_level) 
        defer.returnValue( (user_treasure_id, attrib.item_id, attrib.refine_level, self.user.base_att.golds, items_return, left_items) )
 
    @defer.inlineCallbacks
    def treasure_replace(self, *args):
        '''
        @summary: 更换某宝物
        '''
        camp_id, pos_id, old_utid, new_utid = args

        res_err = UNKNOWN_ERROR

        old_attrib  = yield self.get( old_utid )
        new_attrib  = yield self.get( new_utid )
        if (not old_attrib) or (not new_attrib):
            log.error('Can not find user treasure. old_user_treasure_id: {0}, new_user_treasure_id: {1}.'.format( old_utid, new_utid ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )

        # 检查装备的类型和位置ID是否相符
        if new_attrib.item_type != TREASURE_POSITION_TYPEs.get(pos_id, 0):
            log.error('select treasure type error. item type: {0}.'.format( new_attrib.item_type ))
            defer.returnValue( ITEM_TYPE_ERROR )

        # 删除new_utid对应的旧的阵营信息
        if self.__camp_position.has_key( new_attrib.camp_id ) and \
                self.__camp_position[new_attrib.camp_id].has_key( new_attrib.position_id ):
            del self.__camp_position[new_attrib.camp_id][new_attrib.position_id]

        old_attrib.camp_id     = 0
        old_attrib.position_id = 0

        new_attrib.camp_id     = camp_id
        new_attrib.position_id = pos_id

        # 更新 self.__camp_position data
        if not self.__camp_position.has_key( camp_id ):
            self.__camp_position[camp_id] = {}
        self.__camp_position[camp_id][pos_id] = new_utid

        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def treasure_wear(self, *args):
        '''
        @summary: 穿戴某宝物
        '''
        camp_id, pos_id, user_treasure_id = args

        res_err = UNKNOWN_ERROR

        attrib  = yield self.get( user_treasure_id )
        if not attrib:
            log.error('Can not find user treasure. user_treasure_id: {0}.'.format( user_treasure_id ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )
        
        # 检查装备的类型和位置ID是否相符
        if attrib.item_type != TREASURE_POSITION_TYPEs.get(pos_id, 0):
            log.error('select treasure type error. item type: {0}.'.format( attrib.item_type ))
            defer.returnValue( ITEM_TYPE_ERROR )

        # 删除new_utid对应的旧的阵营信息
        if self.__camp_position.has_key( attrib.camp_id ) and \
                self.__camp_position[attrib.camp_id].has_key( attrib.position_id ):
            del self.__camp_position[attrib.camp_id][attrib.position_id]

        # 指定camp id 和 position id
        attrib.camp_id     = camp_id
        attrib.position_id = pos_id

        # 更新 self.__camp_position 
        if not self.__camp_position.has_key( camp_id ):
            self.__camp_position[camp_id] = {}
        self.__camp_position[camp_id][pos_id] = user_treasure_id

        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def treasure_discard(self, *args):
        '''
        @summary: 卸下某装备
        '''
        camp_id, pos_id, user_treasure_id = args

        res_err = UNKNOWN_TREASURE_ERROR

        attrib  = yield self.get( user_treasure_id )
        if not attrib:
            log.error('Can not find user treasure. user_treasure_id: {0}.'.format( user_treasure_id ))
            defer.returnValue( res_err )
        #检查装备的camp id 和 position id
        if camp_id != attrib.camp_id or pos_id != attrib.position_id:
            log.error('Equip discard error. treasure camp id: {0}, position_id: {1}.'.format( attrib.camp_id, attrib.position_id ))
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

        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def set_one_touch(self, camp_id, args):
        '''
        @summary: 一键装备兵书、战马
        '''
        if not self.__camp_position.has_key( camp_id ):
            _camp_treasure = {}
            self.__camp_position[camp_id] = _camp_treasure
        else:
            _camp_treasure = self.__camp_position[camp_id]

        for _pos_id, _utid in enumerate(args):
            if _utid <= 0:
                continue
            attrib = yield self.get( _utid )
            if not attrib:
                log.error('Can not find user treasure. user_treasure_id: {0}.'.format( _utid ))
                continue

            _pos_id += 6
            # 检查装备的类型和位置ID是否相符
            if attrib.item_type != TREASURE_POSITION_TYPEs.get(_pos_id, 0):
                log.error('select treasure type error. item type: {0}.'.format( attrib.item_type ))
                defer.returnValue( ITEM_TYPE_ERROR )
            if _camp_treasure.has_key( _pos_id ):
                if _camp_treasure[_pos_id] > 0:
                    old_attrib = yield self.get( _camp_treasure[_pos_id] )
                    # 新旧装备ID相同
                    if not old_attrib or old_attrib.attrib_id == _utid:
                        continue
                    old_attrib.camp_id     = 0
                    old_attrib.position_id = 0

            # 指定camp id 和 position id
            attrib.camp_id       = camp_id
            attrib.position_id   = _pos_id 
            # 更新 self.__camp_position
            _camp_treasure[_pos_id] = _utid

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def get_camp_treasure(self, camp_id):
        '''
        @summary: 获取camp_id的position_id对应的treasure
        '''
        yield self._load()
        _camp_treasure = [[], []]

        if not self.__camp_position.has_key(camp_id):
            defer.returnValue( _camp_treasure )

        positions = self.__camp_position[camp_id]

        # 6-兵书, 7-战马
        for _pos in range(6, 8):
            if not positions.has_key(_pos):
                continue
            user_treasure_id = positions[_pos]

            attrib  = yield self.get( user_treasure_id )
            if not attrib:
                log.error('Can not find user treasure. user_treasure_id: {0}.'.format( user_treasure_id ))
                positions[_pos] = 0
                continue
            _camp_treasure[_pos-6] = [user_treasure_id, attrib.item_id, attrib.level, attrib.refine_level]

        defer.returnValue( _camp_treasure )

    @defer.inlineCallbacks
    def gm_get_camp_treasure(self, camp_id):
        ''' GM获取阵容中的宝物详情
        '''
        yield self._load()
        dict_data = [{}, {}]

        if not self.__camp_position.has_key(camp_id):
            defer.returnValue( dict_data )
        positions = self.__camp_position[camp_id]

        # 6-兵书, 7-战马
        for _pos in range(6, 8):
            if not positions.has_key(_pos):
                continue

            user_treasure_id = positions[_pos]
            attrib  = yield self.get( user_treasure_id )
            if not attrib:
                log.error('Can not find user treasure. user_treasure_id: {0}.'.format( user_treasure_id ))
                continue
            dict_data[_pos-6] = {'user_item_id':user_treasure_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'level':attrib.level, 'refine_level':attrib.refine_level}

        defer.returnValue( dict_data )

    @defer.inlineCallbacks
    def gm_treasure_info(self):
        yield self._load()
        _treasure_info = []
        for attrib in self.__gsattribs.itervalues():
            _treasure_info.append( {'user_item_id':attrib.attrib_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'item_cnt':attrib.item_num, 'level':attrib.level, 'refine':[], 'exp':attrib.exp, 'refine_level':attrib.refine_level} )

        defer.returnValue( _treasure_info )


