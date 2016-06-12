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

from twisted.internet.defer import inlineCallbacks, returnValue
from protocol_manager       import protocol_manager
from manager.user           import g_UserMgr

@route()
def registersrv(p, req):
    srv = req
    p.setTimeout( None )
    protocol_manager.set_server(srv, p)
    return (0, 0)

@route()
@inlineCallbacks
def alli_login(p, req):
    res = [ UNKNOWN_ERROR, None ]

    cid, nick_name, level, vip_level, might, rank, lead_id = req

    _m = yield g_UserMgr.login( cid, nick_name, level, vip_level, lead_id, might, rank )
    if _m:
        _alliance = _m.alliance
        res[0] = NO_ERROR
        res[1] = ( _alliance.aid, _alliance.name, _m.position ) if _alliance else ( 0, '', 0 )

    returnValue( res )

@route()
@inlineCallbacks
def alli_logout(p, req):
    cid, = req

    yield g_UserMgr.logout(cid)
    returnValue( NO_ERROR )


