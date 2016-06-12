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
def get_atlaslist_info(p, req):
    ''' 好友留言 '''
    cid, [category_id, second_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.atlaslist_mgr.atlaslist_info(category_id, second_type)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def request_atlaslist_award(p, req):
    ''' 领取星级图鉴收齐后的奖励 '''
    cid, [category_id, second_type, quality] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.atlaslist_mgr.atlaslist_award(category_id, second_type, quality)
    defer.returnValue( res_err )



