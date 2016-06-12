#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from time     import time
from datetime import datetime
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps
from utils    import get_next_refresh_hour, rand_num

from twisted.internet       import defer
from system                 import get_vip_conf, get_mystical_shop_conf
from models.item            import *

ITEM_MODELS = {
           ITEM_TYPE_ITEM: item_add_normal_item,
         ITEM_TYPE_FELLOW: item_add_fellow,
     ITEM_TYPE_FELLOWSOUL: item_add_fellowsoul,
     ITEM_TYPE_EQUIPSHARD: item_add_equipshard,
    #ITEM_TYPE_HORSESHARD: item_add_horseshard,
  #ITEM_TYPE_BOOKWARSHARD: item_add_bookwarshard,
         }


class GSMysticalShopMgr(object):
    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

    @defer.inlineCallbacks
    def mystical_status(self):
        _conf      = get_vip_conf( self.user.base_att.vip_level )
        _max_count = _conf['FreeMaxCount'] if _conf else 2

        _data = yield redis.hget( HASH_MYSTICAL_SHOP, self.cid )
        if _data:
            _last_time, _free_count, _, _  = loads( _data )

            _, _add_count = get_next_refresh_hour( _last_time )
            if _add_count > 0 and _free_count < _max_count:
                _free_count = _max_count if (_free_count + _add_count) >= _max_count else (_free_count + _add_count)
        else:
            _free_count = _max_count

        defer.returnValue( [_free_count, _max_count] )

    @defer.inlineCallbacks
    def mystical_info(self, refresh_type):
        '''
        @summary: 获取神秘商店的刷新时间、道具等信息
        @param  : 0:获取列表,无任何消耗; 1:使用免费次数; 2:使用刷新令道具; 3:使用20钻石
        '''
        _info = []
        _data = yield redis.hget( HASH_MYSTICAL_SHOP, self.cid )
        _conf      = get_vip_conf( self.user.base_att.vip_level )
        _max_count = _conf['FreeMaxCount'] if _conf else 2

        if _data:
            _info    = loads( _data )
            _info[2] = _max_count
        else:
            _items     = yield self.random_items( self.user.base_att.level, self.user.base_att.vip_level )
            _info      = [int(time()), _max_count, _max_count, _items]
            #yield redis.hset( HASH_MYSTICAL_SHOP, self.cid, dumps(_info) )
        # 计算玩家可获得的免费刷新神秘商店的次数
        _next, _add_count = get_next_refresh_hour( _info[0] )
        #log.info('For Test. _next: {0}, _add_count: {1}, _info: {2}.'.format( _next, _add_count, _info ))
        if _add_count > 0 and _info[1] < _info[2]:
            _info[1] = _info[2] if (_info[1] + _add_count) >= _info[2] else (_info[1] + _add_count)
            _info[0] = int(time())
        # 玩家当前拥有刷新令的个数
        _refresh_count, item_attribs = yield self.user.bag_item_mgr.get_items( ITEM_REFRESH_SHOP )
        items_return = []
        # 刷新方式的不同处理
        _freshed = False # 是否有过刷新的标志位
        if refresh_type == MYSTICAL_REFRESH_FREE:
            if _info[1] <=0:
                defer.returnValue( REFRESH_MYSTICAL_SHOP_LIMIT )
            else:
                _info[1] -= 1
                _items    = yield self.random_items( self.user.base_att.level, self.user.base_att.vip_level )
                if _items:
                    _info[3] = _items
                _info[0] = int(time())
                _freshed = True
        elif refresh_type == MYSTICAL_REFRESH_ITEM:
            if _refresh_count <= 0:
                defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            else:
                _refresh_count -= 1
                res_err, used_attribs = yield self.user.bag_item_mgr.use( ITEM_REFRESH_SHOP, 1 )
                if res_err:
                    log.error('Use item error.')
                    defer.returnValue( res_err )
                # used_attribs-已使用的道具
                for _a in used_attribs:
                    items_return.append( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num] )
                _items  = yield self.random_items( self.user.base_att.level, self.user.base_att.vip_level )
                if _items:
                    _info[3] = _items
                _info[0] = int(time())
                _freshed = True
        elif refresh_type == MYSTICAL_REFRESH_CREDITS:
            if self.user.base_att.credits < MYSTICAL_REFRESH_COST:
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            else:
                #self.user.base_att.credits -= MYSTICAL_REFRESH_COST
                yield self.user.consume_credits( MYSTICAL_REFRESH_COST, WAY_MYSTICAL_SHOP )
                _items = yield self.random_items( self.user.base_att.level, self.user.base_att.vip_level )
                if _items:
                    _info[3] = _items
                _info[0] = int(time())
                _freshed = True

        yield redis.hset( HASH_MYSTICAL_SHOP, self.cid, dumps(_info) )
        # 每日任务计数
        if _freshed:
            yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_1, 1 )
            # 开服七天
            yield self.user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_13, 1)
            yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_13, 1)
        _info[0] = _next
        _info.append( _refresh_count )
        _info.append( self.user.base_att.credits )
        _info.append( items_return )
        defer.returnValue( _info )
 
    @defer.inlineCallbacks
    def random_items(self, level, vip_level):
        ''' 从神秘商店中随机8次，每次1个道具，未被随机到的道具概率需要累计 '''
        all_items = get_mystical_shop_conf( level, vip_level )
        if not all_items:
            defer.returnValue( [] )
        flag = False # 是否需要更新redis的标志位
        data = yield redis.hget( HASH_MYSTICAL_LOTTERY, self.cid )
        if data:
            section, mystical_data = loads( data )
            if section != (level, vip_level):
                mystical_data = {}
        else:
            mystical_data = {}

        items_ids  = [] # 已随机的ID
        items_data = [] # 已随机的items
        total_rate = 0  # 总权重值
        items_rate = {} # 临时的id:rate值
        for _id, _item in all_items.iteritems():
            _id_rate = ( _item['Rate'] + _item['RateAdd'] * mystical_data.get(_id, 0) )
            total_rate += _id_rate
            items_rate[_id] = _id_rate

        for _idx in range(0, 8):
            _curr = 0
            _rand = rand_num(total_rate)
            for _id, _item in all_items.iteritems():
                if _rand < (_curr + items_rate[_id]):
                    items_ids.append( _id )
                    items_data.append( [_idx, _item['ItemType'], _item['ItemID'], _item['ItemNum'], _item['CostItemType'], _item['CostItemID'],  _item['CostItemNum'], 1] )
                    break
                else:
                    _curr += items_rate[_id]
            else:
                log.error('No random item. _rand: {0}, total_rate: {1}, _curr: {2}.'.format( _rand, total_rate, _curr ))
                defer.returnValue( [] )

        # 累计次数提高比重
        for _id, _item in all_items.iteritems():
            if _id in items_ids:
                # 已抽中的道具累计次数清零
                if mystical_data.has_key( _id ):
                    del mystical_data[_id]
                    flag = True
                continue
            if (not _item['RateAdd']):
                continue
            # 剩余未抽中的道具累计次数加1
            mystical_data[_id] = mystical_data.setdefault(_id, 0) + 1
            flag = True
        # 保存redis
        if flag:
            yield redis.hset( HASH_MYSTICAL_LOTTERY, self.cid, dumps([(level, vip_level), mystical_data]) )
        defer.returnValue( items_data )

    @defer.inlineCallbacks
    def exchange_item(self, index, item_type, item_id):
        ''' 兑换道具 '''
        _data = yield redis.hget( HASH_MYSTICAL_SHOP, self.cid )
        if not _data:
            log.error('Can not find redis mystical shop data.')
            defer.returnValue( UNKNOWN_ERROR )

        _info = loads( _data )
        if len(_info) != 4 or len(_info[3]) != 8:
            log.error('Mystical item data error. data: {0}.'.format( _info ))
            defer.returnValue( UNKNOWN_ERROR )

        _item = _info[3][index]
        if len(_item) != 8 or item_type != _item[1] or item_id != _item[2]:
            log.error('Mystical item data error. data: {0}.'.format( _info ))
            defer.returnValue( UNKNOWN_ERROR )
        # 判断魂玉和背包容量是否满足
        if _item[7] < 1:
            log.error('Exchange item count limit. _item: {0}.'.format( _item ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        if _item[4] != 1:
            log.error('Char type is wrong.')
            defer.returnValue( ITEM_TYPE_ERROR )

        _model = ITEM_MODELS.get( _item[1], None )
        if not _model:
            log.error('Can not find model. item type: {0}.'.format( _item[1] ))
            defer.returnValue( ITEM_TYPE_ERROR )
            
        if _item[5] == ITEM_MONEY_GOLDS:
            if self.user.golds < _item[6]:
                defer.returnValue(CHAR_GOLD_NOT_ENOUGH)
            self.user.consume_golds(_item[6], WAY_MYSTICAL_SHOP)
            left_num = self.user.golds

        elif _item[5] == ITEM_MONEY_CREDITS:
            if self.user.credits < _item[6]:
                defer.returnValue(CHAR_CREDIT_NOT_ENOUGH)
            self.user.consume_credits(_item[6], WAY_MYSTICAL_SHOP)
            left_num = self.user.credits

        elif _item[5] == ITEM_MONEY_HUNYU:
            if self.user.base_att.hunyu < _item[6]:
                defer.returnValue(CHAR_HUNYU_NOT_ENOUGH)
            self.user.base_att.hunyu -= _item[6]
            left_num = self.user.base_att.hunyu
        else:
            defer.returnValue(ITEM_TYPE_ERROR)
        # 新增道具
        _conf = {'ItemID': _item[2], 'ItemNum': _item[3], 'AddType': WAY_MYSTICAL_SHOP, 'CapacityFlag': False}
        res_err, value = yield _model(self.user, **_conf)
        if res_err:
            defer.returnValue( res_err )

        # 更新redis的数据
        _item[7] = (_item[7]-1) if _item[7] > 0 else 0
        yield redis.hset( HASH_MYSTICAL_SHOP, self.cid, dumps( _info ))

        defer.returnValue( [_item[4], _item[5], left_num, value] )



