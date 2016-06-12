#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 活动公共的模块, 活动包含竞技场、夺宝、比武
#         公共部分包含阵容的获取, 翻牌抽3个道具

import random

from log      import log
from marshal  import loads, dumps     

from errorno  import *
from constant import *
from redis    import redis
from utils    import rand_num
from system   import get_activity_lottery

from twisted.internet        import defer, reactor
from handler.character       import gs_offline_login, gs_offline_logout


#@defer.inlineCallbacks
#def load_camp(cid):
#    ''' 获取玩家的阵容, 不含机器人 '''
#    data = yield redis.hget( HASH_CHARACTER_CAMP, cid )
#    if not data:
#        data = yield redis.hget( HASH_TREASURE_CHARACTER_CAMP, cid )
#
#    if data:
#        data = loads( data )
#    else:
#        log.error('No camp data. cid: {0}.'.format( cid ))
#
#    defer.returnValue( data )
#
#@defer.inlineCallbacks
#def load_camp_fellow_ids(cid, camp_type):
#    ''' 
#    @summary: 加载玩家阵容的伙伴ID 
#    @param  : camp_type-1:竞技场排行榜中的玩家; 2:拥有宝物碎片的玩家
#    '''
#    if camp_type == 1:
#        _key = HASH_CHARACTER_CAMP
#    else:
#        _key = HASH_TREASURE_CHARACTER_CAMP
#    major_level = 0
#    fellow_ids  = []
#    data        = yield redis.hget( _key, cid )
#    if data:
#        data = loads( data )
#        for camp_data in data[1]:
#            if not camp_data or not camp_data[1]:
#                continue
#            # 获取主角的最新等级
#            if camp_data[1][1] < 10:
#                major_level = camp_data[1][2]
#            fellow_ids.append( camp_data[1][1] )
#        if not fellow_ids:
#            log.error('No char camp data. cid: {0}, camp_type: {1}.'.format( cid, camp_type ))
#            yield redis.hdel( _key, cid )
#    else:
#        log.error('No char camp data. cid: {0}, camp_type: {1}.'.format( cid, camp_type ))
#
#    defer.returnValue( (major_level, fellow_ids) )

@defer.inlineCallbacks
def load_offline_user_info(cid):
    ''' 
    @summary: 加载玩家阵容的伙伴ID 
    '''
    res_err = [1, [], 1]
    offline_user = yield gs_offline_login( cid )
    if offline_user:
        res_err[0] = offline_user.level
        res_err[1] = yield offline_user.fellow_mgr.get_camp_fellow_id()
        res_err[2] = offline_user.lead_id
        reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, cid)

    defer.returnValue( res_err )

@defer.inlineCallbacks
def random_lottery_items(cid, level, vip_level, rand_count=3):
    '''
    @summary: activity翻牌的共用
    @param  : rand_count-3为默认幸运道具个数
    @param  : HASH_ACTIVITY_LOTTERY cid dumps((level, vip_level), {ID: count})
    '''
    all_items = get_activity_lottery(level, vip_level)
    if not all_items:
        log.error("No activity lottery conf. cid: {0}, level: {1}, vip_level: {2}.".format( cid, level, vip_level ))
        defer.returnValue( [] )

    flag = False # 是否需要更新redis的标志位
    data = yield redis.hget( HASH_ACTIVITY_LOTTERY, cid )
    if data:
        section, lottery_data = loads( data )
        if section != (level, vip_level):
            lottery_data = {}
    else:
        lottery_data = {}

    items_ids  = [] # 已随机的ID
    items_data = [] # 已随机的items
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
                    items_data.append( [_conf['ItemType'], _conf['ItemID'], _conf['ItemNum'], _conf['Notice']] )
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
        yield redis.hset( HASH_ACTIVITY_LOTTERY, cid, dumps([(level, vip_level), lottery_data]) )
 
    if not items_data:
        log.error("No activity lottery items. cid: {0}.".format( cid ))
    defer.returnValue( items_data )

