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
def get_achievement_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.achievement_mgr.status()
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_achievement_reward(p, req):
    cid, [acType, reward_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.achievement_mgr.get_reward( acType, reward_id )

    defer.returnValue( res_err )

