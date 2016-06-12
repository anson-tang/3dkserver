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

from twisted.internet     import defer
from protocol_manager     import protocol_manager
from manager.messageuser  import g_UserMgr



@route()
def registersrv(p, req):
    srv = req
    p.setTimeout( None )
    protocol_manager.set_server(srv, p)
    return (0, 0)

@route()
def ms_login(p, req):
    res_err = UNKNOWN_ERROR

    cid, nick_name, lead_id, vip_level, level, might, alliance_info = req

    _user = g_UserMgr.login(cid, nick_name, lead_id, vip_level, level, might, alliance_info)
    if _user:
        res_err = NO_ERROR

    return res_err

@route()
def ms_logout(p, req):
    cid, = req

    g_UserMgr.logout(cid)

    return NO_ERROR


