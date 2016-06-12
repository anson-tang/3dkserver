#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time              import time
from rpc               import route
from log               import log
from errorno           import *
from constant          import *
from twisted.internet  import defer
from manager.gsuser    import g_UserMgr
from redis             import redis
from utils             import get_reward_timestamp
from system            import get_game_limit_value, get_fellow_by_fid
from time              import time

@route()
@defer.inlineCallbacks
def fellow_list(p, req):
    ''' 获取玩家的伙伴列表 '''
    res_err  = UNKNOWN_ERROR
    
    cid, [idx] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.fellow_mgr.value_list
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_fellow_visual_data(p, req):
    ''' 查看玩家的伙伴信息 '''
    res_err  = UNKNOWN_ERROR
    
    cid, [user_fellow_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.fellow_mgr.value(user_fellow_id)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_fellow_formation(p, req):
    ''' 获取玩家的布阵信息 '''
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.fellow_mgr.get_formation()
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_fellow_formation(p, req):
    ''' 玩家布阵 '''
    res_err = UNKNOWN_ERROR
    
    cid, list_formation = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.fellow_mgr.set_formation( list_formation )
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def fellow_level_upgrade(p, req):
    ''' 伙伴强化 '''
    res_err = CONNECTION_LOSE

    cid, [target_fellow_id, upgrade_type, upgrade_info] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if 1 == upgrade_type:
        res_err = yield user.fellow_mgr.strengthen_by_card( target_fellow_id, upgrade_info )
    elif 2 == upgrade_type:
        res_err = yield user.fellow_mgr.strengthen_by_soul( target_fellow_id, upgrade_info )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def fellow_advanced(p, req):
    ''' 伙伴进阶 '''
    res_err = CONNECTION_LOSE

    cid, [target_ufid] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.fellow_mgr.advanced( target_ufid )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_camp_fellow(p, req):
    ''' 新增、更换阵容中的伙伴 '''
    res_err = CONNECTION_LOSE

    cid, [camp_id, old_ufid, new_ufid] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.fellow_mgr.set_camp_fellow(camp_id, old_ufid, new_ufid)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def rescue_er_lang_god(p, req):
    ''' 解除二郎神封印 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # check stataus
    end_timestamp = yield redis.hget(HASH_RESCUE_ER_LANG_GOD, cid)
    if end_timestamp:
        defer.returnValue( [end_timestamp] )

    # end timestamp
    end_timestamp = get_reward_timestamp(0)
    yield redis.hset(HASH_RESCUE_ER_LANG_GOD, cid, end_timestamp)

    defer.returnValue( [end_timestamp] )

@route()
@defer.inlineCallbacks
def get_er_lang_god(p, req):
    ''' 领取二郎神 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # check stataus
    end_timestamp = yield redis.hget(HASH_RESCUE_ER_LANG_GOD, cid)
    if -1 == end_timestamp:
        defer.returnValue( REPEAT_REWARD_ERROR )

    limit_vip_level = get_game_limit_value( LIMIT_ID_ER_LANG_VIP_LEVEL )
    if not limit_vip_level or user.vip_level < limit_vip_level:
        now = int(time())
        if not end_timestamp or end_timestamp > now:
            defer.returnValue( REQUEST_LIMIT_ERROR )

    # give er-lang god
    end_timestamp = -1
    yield redis.hset(HASH_RESCUE_ER_LANG_GOD, cid, end_timestamp)

    fellow_id = get_game_limit_value( LIMIT_ID_ER_LANG_GOD_ID )
    fellow_conf = get_fellow_by_fid( fellow_id )
    if not fellow_conf:
        defer.returnValue( UNKNOWN_FELLOW_ERROR )

    res_err, attrib = yield user.fellow_mgr.create_table_data( fellow_id, 0, 0, 0 )
    if res_err or not attrib:
        defer.returnValue( UNKNOWN_ERROR )

    defer.returnValue( [attrib.attrib_id, attrib.fellow_id, end_timestamp] )



