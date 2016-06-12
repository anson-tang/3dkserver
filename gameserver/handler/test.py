#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


from rpc                 import route
from twisted.internet    import defer, reactor
from log                 import log
from errorno             import *
from constant            import *
from redis               import redis
from system              import get_activity_lottery
from utils               import rand_num


@route()
@defer.inlineCallbacks
def gs_gm_test_random_item(p, req):
    '''
    @summary: activity翻牌的共用
    @param  : rand_count-3为默认幸运道具个数
    @param  : HASH_ACTIVITY_LOTTERY cid dumps((level, vip_level), {ID: count})
    '''
    level, vip_level, rand_count = req[0]

    rand_count = int(rand_count)

    all_items = get_activity_lottery(int(level), int(vip_level))
    if not all_items:
        log.error("No activity lottery conf. level: {1}, vip_level: {2}.".format( level, vip_level ))
        defer.returnValue( [] )

    flag = False # 是否需要更新redis的标志位
    data = yield redis.get( 'KEY_TEST_RANDOM_ITEM' )
    if data:
        section, lottery_data = loads( data )
        if section != (level, vip_level):
            lottery_data = {}
    else:
        lottery_data = {}

    items_ids  = [] # 已随机的ID
    items_data = {} # 已随机的items
    total_rate = 0
    items_rate = {} # 临时的id:rate值
    for _id, _item in all_items.iteritems():
        _id_rate = _item['Rate'] + _item['AddRate'] * lottery_data.get(_id, 0)
        total_rate += _id_rate
        items_rate[_id] = _id_rate

    if total_rate > 0:
        for i in range(0, rand_count):
            curr_int = 0
            randint = rand_num(total_rate)
            for _id, _conf in all_items.iteritems():
                if randint < (curr_int + items_rate[_id]):
                    items_ids.append( _id )
                    if not items_data.has_key( _id ):
                        items_data[_id] = [_conf['ID'], _conf['RoleLevel'], _conf['VipLevel'], _conf['ItemType'], _conf['ItemID'], _conf['ItemNum'], _conf['Rate'], _conf['AddRate'], _conf['ActiveID'], 1]
                    else:
                        items_data[_id][-1] += 1

                    #log.error('For Test. randint: {0}, total_rate: {1}, curr_int: {2}, items_ids: {3}.'.format( randint, total_rate, curr_int, items_ids ))
                    break
                else:
                    curr_int += items_rate[_id]
            else:
                log.error('No random item. randint: {0}, total_rate: {1}, curr_int: {2}.'.format( randint, total_rate, curr_int ))
                defer.returnValue( [] )
    else:
        log.error('Activity lottery pool is null. total_rate: {0}.'.format( total_rate ))
        defer.returnValue( [] )

    # 累计次数提高比重
    for _id, _item in all_items.iteritems():
        if _id in items_ids:
            # 已抽中的道具累计次数清零
            if lottery_data.has_key( _id ):
                del lottery_data[_id]
                flag = True
            continue
        if (not _item['AddRate']):
            continue
        # 剩余未抽中的道具累计次数加1
        lottery_data[_id] = lottery_data.setdefault(_id, 0) + 1
        flag = True
    # 保存redis
    if flag:
        yield redis.set( 'KEY_TEST_RANDOM_ITEM', dumps([(level, vip_level), lottery_data]) )
 
    if not items_data:
        log.error("No activity lottery items. cid: {0}.".format( cid ))
    defer.returnValue( items_data.values() )



