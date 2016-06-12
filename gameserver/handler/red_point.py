#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


from twisted.internet    import defer, reactor
from manager.gsuser      import g_UserMgr

from rpc        import route
from log        import log
from errorno    import *
from constant   import *




@route()
def red_point_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( (CONNECTION_LOSE, []) )


    res_err = {'alliance': user.alliance_id}
    return res_err


