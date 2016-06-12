#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from twisted.internet    import defer, reactor


from rpc        import route
from log        import log
from errorno    import *
from constant   import *

from manager.gsuser      import g_UserMgr



@route()
@defer.inlineCallbacks
def daily_quest_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.daily_quest_mgr.status()
    if isinstance(res_err, (tuple, list)):
        defer.returnValue( res_err[1:] )
    else:
        defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_daily_quest_reward(p, req):
    cid, [reward_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.daily_quest_mgr.get_reward( reward_id )

    defer.returnValue( res_err )


@route()
@defer.inlineCallbacks
def get_quest_reward(p, req):
    cid, [quest_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.daily_quest_mgr.get_daily_quest_reward(quest_id)
    defer.returnValue( res_err )
