#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from rpc      import route
from log      import log
from errorno  import *
from constant import *

from twisted.internet import defer
from manager.gsuser   import g_UserMgr
from syslogger        import syslogger

@route()
@defer.inlineCallbacks
def climbing_tower_data(p, req):
    res_err = UNKNOWN_ERROR

    cid, [req_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    if req_type: # 重置
        res_err = yield user.climbing_tower_mgr.reset_climbing()
    else: # 获取基本信息
        res_err = yield user.climbing_tower_mgr.climbing_data()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def buy_climbing_count(p, req):
    res_err = UNKNOWN_ERROR

    cid, [count_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.climbing_tower_mgr.buy_count( count_type )

    defer.returnValue( res_err )
 
@route()
@defer.inlineCallbacks
def get_climbing_reward(p, req):
    res_err = UNKNOWN_ERROR

    cid, [fight_layer, status] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.climbing_tower_mgr.climbing_reward( fight_layer, status )
    syslogger(LOG_CLIMB_TOWER, cid, user.level, user.vip_level, user.alliance_id, user.climbing_tower_mgr.climbing.cur_layer, WAY_CLIMB_TOWER_SINGLE)

    defer.returnValue( res_err )
 
@route()
def start_climbing(p, req):
    res_err = UNKNOWN_ERROR

    cid, [fight_layer]= req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return res_err

    res_err = user.climbing_tower_mgr.start_climbing(fight_layer)
    syslogger(LOG_CLIMB_TOWER, cid, user.level, user.vip_level, user.alliance_id, user.climbing_tower_mgr.climbing.cur_layer, WAY_CLIMB_TOWER_START)
    return res_err

@route() 
@defer.inlineCallbacks
def stop_climbing(p, req):
    res_err = UNKNOWN_ERROR

    cid, [stop_layer] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.climbing_tower_mgr.stop_climbing( stop_layer )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def finish_climbing(p, req):
    res_err = UNKNOWN_ERROR

    cid, [fight_layer]= req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.climbing_tower_mgr.finish_climbing( fight_layer )
    syslogger(LOG_CLIMB_TOWER, cid, user.level, user.vip_level, user.alliance_id, user.climbing_tower_mgr.climbing.cur_layer, WAY_CLIMB_TOWER_FINISH)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_climbing_ranklist(p, req):
    ''' 获取天外天的排行榜 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.climbing_tower_mgr.ranklist()

    defer.returnValue( res_err )

