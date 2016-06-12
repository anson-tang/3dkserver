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
from utils    import datetime2string
from marshal  import loads, dumps
from redis    import redis

from syslogger              import syslogger
from twisted.internet       import defer
from system                 import get_item_by_itemid, get_random_chest_conf
from manager.gsattribute    import GSAttribute
from models.item            import *
from models.randpackage     import package_open
from protocol_manager       import gw_broadcast


class GSBagItemMgr(object):
    '''
    @summary: 玩家道具背包
    '''
    _table  = 'bag_item'

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        self.__gsattribs = None

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def _load(self):
        if self.__gsattribs is None:
            if not self.__loading:
                self.__loading = True
                self.__gsattribs = yield GSAttribute.load( self.cid, GSBagItemMgr._table )

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
    def get_items(self, item_id, user_item_id=0):
        '''
        @param  : user_item_id-是否需要排除的uid, 默认不排除
        @return : total_num-item id的总数; item_attribs-item id 对应的所有attrib, 数量按照数量多少排序 
        '''
        yield self._load()
        total_num, item_attribs = 0, []
        # 获取item id的最大叠加数
        item_conf = get_item_by_itemid( item_id )
        if not item_conf:
            log.error('Can not find conf. item_id: {0}.'.format( item_id ))
            defer.returnValue( (total_num, item_attribs) )
        MAX_NUM = item_conf['MaxOverlyingCount']

        for attrib in self.__gsattribs.itervalues():
            if attrib.item_id == item_id and attrib.item_num > 0:
                total_num += attrib.item_num
                if attrib.item_num < MAX_NUM:
                    item_attribs.insert(0, attrib)
                else:
                    item_attribs.append( attrib )

        defer.returnValue( (total_num, item_attribs) )

    @defer.inlineCallbacks
    def get(self, user_item_id):
        yield self._load()
        defer.returnValue( self.__gsattribs.get(user_item_id, None) )

    @defer.inlineCallbacks
    def cur_capacity(self):
        yield self._load()
        defer.returnValue( len(self.__gsattribs) )

    @property
    @defer.inlineCallbacks
    def value_list(self):
        yield self._load()
        value_list = []
        for attrib in self.__gsattribs.itervalues():
            value_list.append( (attrib.attrib_id, attrib.item_id, attrib.item_num) )

        defer.returnValue( (len(value_list), value_list) )

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
        if item_type not in BAG_ITEM:
            log.error('new. Item type error. item_id: {0}.'.format( item_id ))
            defer.returnValue( (ITEM_TYPE_ERROR, None) )

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
                errorno, new_attrib = yield self.create_table_data(item_type, item_id, MAX_NUM, time_now)
                if errorno:
                    defer.returnValue( (UNKNOWN_ERROR, None) )
                cur_item_num -= MAX_NUM
                new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, MAX_NUM], new_items )
            else:
                if cur_item_num > 0:
                    errorno, new_attrib = yield self.create_table_data(item_type, item_id, cur_item_num, time_now)
                    if errorno:
                        defer.returnValue( (UNKNOWN_ERROR, None) )
                    new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, cur_item_num], new_items )

        # add syslog
        for _item in new_items:
            syslogger(LOG_ITEM_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _item[0], _item[2], _item[3], way_type, way_others)
        defer.returnValue( (NO_ERROR, new_items) )

    @defer.inlineCallbacks
    def create_table_data(self, item_type, item_id, item_num, time_now):
        gsattrib = GSAttribute( self.cid, GSBagItemMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, item_type=item_type, item_id=item_id, item_num=item_num, deleted=0, create_time=time_now, update_time=time_now, del_time=0, aux_data='' )
        if res_err:
            log.error('GSBagItemMgr create table data error. ')
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
    def guanxing(self):
        yield self._load()

        cnt = 0

        for attrib in self.__gsattribs.itervalues():
            if attrib.item_id == ITEM_GUANXINGLING:
                cnt = attrib.item_num
                break

        defer.returnValue( cnt )

    @defer.inlineCallbacks
    def use(self, item_id, item_num):
        '''
        @summary: 先使用数量少的, 接着使用已满叠加数的道具
        '''
        # used item attrib
        used_attribs = []
        total_num, item_attribs = yield self.get_items( item_id )
        if item_num > total_num:
            log.error('Item id: {0}, need num: {1}, cur num: {2}.'.format( item_id, item_num, total_num ))
            defer.returnValue( [CHAR_ITEM_NOT_ENOUGH, used_attribs] )

        for attrib in item_attribs:
            if attrib.item_num < item_num:
                item_num -= attrib.item_num
                attrib.item_num = 0
            else:
                attrib.item_num -= item_num
                item_num = 0
            # save used item attrib
            used_attribs.append( attrib )

            if attrib.item_num == 0:
                self.delete_table_data( attrib.attrib_id )

            if 0 == item_num:
                break

        defer.returnValue( (NO_ERROR, used_attribs) )

    @defer.inlineCallbacks
    def chest_use(self, chest_item_id, key_item_id, chest_item_num, key_item_num):
        '''
        @summary: 先使用数量少的, 接着使用已满叠加数的道具
        '''
        # used item attrib
        used_attribs = []
        total_chest_num, chest_attribs = yield self.get_items( chest_item_id )
        if chest_item_num > total_chest_num:
            log.error('Chest item id: {0}, need num: {1}, cur num: {2}.'.format( chest_item_id, chest_item_num, total_chest_num ))
            defer.returnValue( [CHAR_ITEM_NOT_ENOUGH, used_attribs] )

        total_key_item, key_attribs = yield self.get_items( key_item_id )
        if key_item_num > total_key_item:
            log.error('Item id: {0}, need num: {1}, cur num: {2}.'.format( key_item_id, key_item_num, total_key_item ))
            defer.returnValue( [CHAR_ITEM_NOT_ENOUGH, used_attribs] )

        # 检查背包容量
        res_err = yield check_bag_capacity( self.user )
        if res_err:
            log.error('User bag capacity not enough. res_err: {0}.'.format( res_err ))
            defer.returnValue( [res_err, used_attribs] )

        for attrib in chest_attribs:
            if attrib.item_num < chest_item_num:
                chest_item_num -= attrib.item_num
                attrib.item_num = 0
            else:
                attrib.item_num -= chest_item_num
                chest_item_num = 0
            # save used item attrib
            used_attribs.append( attrib )

            if attrib.item_num == 0:
                self.delete_table_data( attrib.attrib_id )

            if 0 == chest_item_num:
                break

        for attrib in key_attribs:
            if attrib.item_num < key_item_num:
                key_item_num -= attrib.item_num
                attrib.item_num = 0
            else:
                attrib.item_num -= key_item_num
                key_item_num = 0
            # save used item attrib
            used_attribs.append( attrib )

            if attrib.item_num == 0:
                self.delete_table_data( attrib.attrib_id )

            if 0 == key_item_num:
                break

        defer.returnValue( (NO_ERROR, used_attribs) )

    @defer.inlineCallbacks
    def item_use(self, item_id, item_num):
        '''
        @summary: 背包中使用道具
        '''
        res_err = UNKNOWN_ITEM_ERROR
        # 按照类型使用道具
        item_conf = get_item_by_itemid( item_id )
        if not item_conf:
            log.error('Can not find conf. item_id: {0}.'.format( item_id ))
            defer.returnValue( res_err )
        if not item_conf['IsUsed'] or (item_conf['ItemType'] not in BAG_ITEM):
            log.error('Can not use item. item_id: {0}, item_conf: {1}.'.format( item_id, item_conf ))
            defer.returnValue( ITEM_USER_ERROR )
 
        add_type = WAY_ITEM_USE
        items_return = [] # 剩余的玩家道具信息
        add_items    = [] # 新增的玩家道具信息
        items_list = item_conf['ChangeList']
        if item_conf['ItemType'] in (ITEM_TYPE_CHEST, ITEM_TYPE_KEY):
            add_type = WAY_USE_CHEST
            # 使用宝箱
            if item_conf['ItemType'] == ITEM_TYPE_CHEST: 
                if not items_list: # 不需要使用钥匙
                    chest_item_id = item_id
                    res_err, used_attribs = yield self.use(chest_item_id, item_num)
                else: # 需要钥匙
                    if len(items_list) != 1:
                        log.error('Unknown chest item. item_conf: {0}.'.format( item_conf ))
                        defer.returnValue( res_err )
                    chest_item_id, key_item_id = item_id, items_list[0][1]
                    res_err, used_attribs = yield self.chest_use(chest_item_id, key_item_id, item_num, item_num)
            # 使用钥匙
            else:
                if len(items_list) != 1:
                    log.error('Unknown key item. item_conf: {0}.'.format( item_conf ))
                    defer.returnValue( res_err )
                chest_item_id, key_item_id = items_list[0][1], item_id
                res_err, used_attribs = yield self.chest_use(chest_item_id, key_item_id, item_num, item_num)

            if res_err:
                log.error('Use item error.')
                defer.returnValue( res_err )
            # 根据chest_item_id随机道具
            new_items = yield self.random_chest( chest_item_id, item_num )
        else:
            if not items_list:
                log.error('Can not use item. item_id: {0}, item_conf: {1}.'.format( item_id, item_conf ))
                defer.returnValue( ITEM_USER_ERROR )

            res_err, used_attribs = yield self.use(item_id, item_num)
            if res_err:
                log.error('Use item error.')
                defer.returnValue( res_err )
            # 获取的新道具信息
            new_items = []
            for _type, _id, _num in items_list:
                new_items.append( [_type, _id, _num * item_num] )

        for _a in used_attribs:
            items_return = total_new_items( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num], items_return )

        for _type, _id, _num in new_items:
            _model = ITEM_MODELs.get(_type, None)
            if not _model:
                log.error('Unknown item type. ItemType: {0}.'.format( _type ))
                continue
            res_err, value = yield _model(self.user, ItemID=_id, ItemNum=_num, CapacityFlag=False, AddType=add_type, WayOthers=str((item_id, item_num)))
            if not res_err and value:
                add_items.extend( value )
            else:
                log.warn('User add items error. res_err: {0}, value: {1}.'.format( res_err, value ))
        #res_data = yield batch_items_add(self.user, new_items, add_type, str((item_id, item_num)))
        #for _status, (res_err, value) in res_data:
        #    if not res_err and value:
        #        add_items.extend( value )
        #    else:
        #        log.warn('User add items error. res_err: {0}, value: {1}.'.format( res_err, value ))

        # add syslog
        syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, 0, item_id, item_num, add_type)
        defer.returnValue( (items_return, add_items) )

    @defer.inlineCallbacks
    def random_chest(self, chest_id, chest_num):
        '''
        @summary: 开宝箱时随机道具
        @return : new_items=[[type, id, num], ...]
        '''
        new_items    = []
        msg_item_ids = [] # 需要走马灯通告的道具信息
            
        i = 0
        while i < chest_num:
            i += 1

            _item_rand = yield package_open(self.user, chest_id)

            if _item_rand:
                _item_type, _item_id, _item_num, _notice = _item_rand
                new_items.append((_item_type, _item_id, _item_num))

                if _notice:
                    msg_item_ids.append((_item_type, _item_id, _item_num))

        if msg_item_ids:
            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_RARE_ITEM, [self.user.nick_name, chest_id, msg_item_ids]]]
            gw_broadcast('sync_broadcast', [message])

        log.info('random items length: {0}.'.format( len(new_items) ))
        defer.returnValue( new_items )

    @defer.inlineCallbacks
    def random_chest_old(self, chest_id, chest_num):
        '''
        @summary: 开宝箱时随机道具
        @return : new_items=[[type, id, num], ...]
        '''
        new_items    = []
        msg_item_ids = [] # 需要走马灯通告的道具信息
        conf = get_random_chest_conf( chest_id )
        if not conf:
            log.error('No random_chest conf. chest_id: {0}.'.format( chest_id ))
            defer.returnValue( new_items )

        data = yield redis.hget( HASH_RANDOM_CHEST % chest_id,  self.cid )
        if data:
            data = loads(data)
        else:
            data = {}

        for _i in range(0, chest_num):
            chest_pool = []
            for _id, _value in conf.iteritems():
                _rate = _value['Rate'] + data.get(_id, data.setdefault(_id, 0))
                _rate = _value['MaxRate'] if _rate > _value['MaxRate'] else _rate
                chest_pool.extend( [_id] * _rate )

            if not chest_pool:
                log.error('No random_chest pool. chest_id: {0}.'.format( chest_id ))
                continue

            rand_id = random.choice( chest_pool )
            # 更新rate
            for _id, _value in conf.iteritems():
                if _id == rand_id:
                    data[_id] = 0
                    new_items.append( [_value['ItemType'], _value['ItemID'], _value['ItemNum']] )
                    if _value['Notice']:
                        msg_item_ids.append( [_value['ItemType'], _value['ItemID'], _value['ItemNum']] )
                else:
                    data[_id] += _value['AddRate']

        yield redis.hset( HASH_RANDOM_CHEST % chest_id, self.cid, dumps(data) )
        # 在线广播玩家开宝箱得到稀有道具
        if msg_item_ids:
            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_RARE_ITEM, [self.user.base_att.nick_name, chest_id, msg_item_ids]]]
            gw_broadcast('sync_broadcast', [message])

        log.debug('random items length: {0}.'.format( len(new_items) ))
        defer.returnValue( new_items )

    @defer.inlineCallbacks
    def get_sell_back_cost(self, *args):
        '''
        @summary: 出售道具时返还消耗的金币
        '''
        user_item_ids, = args

        res_err = [UNKNOWN_ITEM_ERROR, 0]
        for _uid in user_item_ids:
            attrib  = yield self.get( _uid )
            if not attrib:
                defer.returnValue( res_err )

            item_conf = get_item_by_itemid( attrib.item_id )
            if not item_conf:
                defer.returnValue( res_err )
            if not item_conf['Price']:
                res_err[0] = ITEM_CANNOT_SELL
                defer.returnValue( res_err )

            res_err[1] += item_conf['Price'] * attrib.item_num

        for _uid in user_item_ids:
            self.delete_table_data( _uid )

        res_err[0] = NO_ERROR
        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def gm_item_info(self):
        yield self._load()
        _item_info = []
        for attrib in self.__gsattribs.itervalues():
            _item_info.append( {'user_item_id':attrib.attrib_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'item_cnt':attrib.item_num, 'level':0, 'refine':[], 'exp':0, 'refine_level':0} )

        defer.returnValue( _item_info )


