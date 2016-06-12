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
def equipshard_list(p, req):
    res_err = UNKNOWN_ERROR
    
    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _len, value_list = yield user.bag_equipshard_mgr.value_list
    max_capacity     = user.base_att.equipshard_capacity
    defer.returnValue( (_len, max_capacity, value_list) )

@route()
@defer.inlineCallbacks
def equipshard_combine(p, req):
    res_err = UNKNOWN_ERROR

    cid, [user_equipshard_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err, equip_id = yield user.bag_equipshard_mgr.combine( user_equipshard_id )
    log.debug('equipshard_combine. res: {0}.'.format( (res_err, equip_id) ))
    if not res_err:
        res_err, value = yield user.bag_equip_mgr.new( equip_id, 1 )
        if not res_err:
            defer.returnValue( (value[0][0], value[0][2]) )
            #defer.returnValue( (value.attrib_id, value.item_id) )

    defer.returnValue( res_err )

