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

@route()
@defer.inlineCallbacks
def constellation_status(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        # 检查是否需要0点更新
        if con_mgr.need_refresh:
            yield con_mgr.reward_to_center()
            yield con_mgr.sync()
            user.constellation_mgr = None
            con_mgr = yield user.constellation
        res = con_mgr.value

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def constellation_select(p, req):
    res = UNKNOWN_ERROR

    #同时兼容新旧协议， 当旧协议时，is_highlight置为-1:未知, 其他状态： 0：未亮， 1：高亮
    try:
        cid, ( star_id, is_highlight ) = req
    except:
        cid, ( star_id, ) = req
        is_highlight = -1

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        # 检查是否需要0点更新
        if con_mgr.need_refresh:
            defer.returnValue( CONSTELLATION_NEED_REFRESH )

        if con_mgr.select_count < CONSTELLATION_SELECT_MAX:
            res = con_mgr.select( int( star_id ), int( is_highlight ) )
            # 每日任务计数
            yield user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_7, 1 )
        else:
            res = CONSTELLATION_SELECT_REACH_MAX

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def constellation_refresh(p, req):
    res = UNKNOWN_ERROR

    cid, ( use_item, ) = req

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        # 检查是否需要0点更新
        if con_mgr.need_refresh:
            defer.returnValue( CONSTELLATION_NEED_REFRESH )

        res, data = yield con_mgr.refresh( user, int( use_item ) )
        res = res if res else data

    defer.returnValue(res)

@route()
@defer.inlineCallbacks
def constellation_reward_status(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        ## 检查是否需要0点更新
        #if con_mgr.need_refresh:
        #    defer.returnValue( CONSTELLATION_NEED_REFRESH )

        res = con_mgr.rewards

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def constellation_reward_refresh(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        # 检查是否需要0点更新
        if con_mgr.need_refresh:
            defer.returnValue( CONSTELLATION_NEED_REFRESH )

        res, data = yield con_mgr.refresh_rewards( user )
        if not res:
            res = data

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def constellation_reward_receive(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        # 检查是否需要0点更新
        if con_mgr.need_refresh:
            defer.returnValue( CONSTELLATION_NEED_REFRESH )

        res = yield con_mgr.receive_reward( user )
        if not res[0]:
            res = res[1:]

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def constellation_onekey_reward_receive(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        con_mgr = yield user.constellation
        # 检查是否需要0点更新
        if con_mgr.need_refresh:
            defer.returnValue( CONSTELLATION_NEED_REFRESH )

        res = yield con_mgr.onekey_receive_reward( user )
        if res[0]:
            res = res[0]
        else:
            res = res[1:]

    defer.returnValue( res )

