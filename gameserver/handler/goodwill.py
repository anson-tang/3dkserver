#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from twisted.internet    import defer, reactor
from manager.gsuser      import g_UserMgr


from rpc        import route
from log        import log
from errorno    import *
from constant   import *



@route()
@defer.inlineCallbacks
def fellow_goodwill_list(p, req):
    ''' 获取神将薄列表 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.goodwill_mgr.get_goodwill_list()
    #成就
    yield user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_23, res_err[0])

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def gift_fellow_goodwill(p, req):
    ''' 赠送神将好感度 '''
    cid, [fellow_id, use_items] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    
    if not use_items:
        defer.returnValue( GOODWILL_ITEM_ERROR )

    res_err = yield user.goodwill_mgr.gift_goodwill(fellow_id, use_items)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def exchange_goodwill_level(p, req):
    ''' 互换好感度等级 '''
    cid, [left_fellow_id, right_fellow_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.goodwill_mgr.exchange_goodwill(left_fellow_id, right_fellow_id)

    defer.returnValue( res_err )


