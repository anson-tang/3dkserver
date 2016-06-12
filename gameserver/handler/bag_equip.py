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
def equip_list(p, req):
    res_err = UNKNOWN_ERROR

    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _len, value_list = yield user.bag_equip_mgr.value_list
    max_capacity     = user.base_att.equip_capacity
    defer.returnValue( (_len, max_capacity, value_list) )

@route()
@defer.inlineCallbacks
def equip_strengthen(p, req):
    res_err = UNKNOWN_ERROR

    cid, [user_equip_id, strengthen_type] = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    if strengthen_type not in [STRENGTHEN_NORMAL, STRENGTHEN_AUTO]:
        log.error('Equip strengthen type error. strengthen type: {0}.'.format( strengthen_type ))
        defer.returnValue( res_err )

    res_err = yield user.bag_equip_mgr.strengthen( user_equip_id, strengthen_type )
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def equip_refine(p, req):
    res_err = UNKNOWN_ERROR

    cid, refine_args = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    res_err = yield user.bag_equip_mgr.refine( refine_args )
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def equip_refine_replace(p, req):
    res_err = UNKNOWN_ERROR

    cid, [user_equip_id, refine_attribute] = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
 
    res_err = yield user.bag_equip_mgr.refine_replace( user_equip_id, refine_attribute )
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_camp_equip(p, req):
    res_err = UNKNOWN_ERROR

    cid, [camp_id, pos_id, old_ueid, new_ueid] = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    # 玩家装备ID不能同时为空
    if not (old_ueid or new_ueid):
        log.error('set equip error. old_ueid and new_ueid could not be all null.')
        defer.returnValue( CLIENT_DATA_ERROR )
    elif old_ueid and new_ueid: # 更换
        res_err = yield user.bag_equip_mgr.equip_replace( camp_id, pos_id, old_ueid, new_ueid )
    elif new_ueid: # 新增
        res_err = yield user.bag_equip_mgr.equip_wear( camp_id, pos_id, new_ueid )
    else: # 卸下
        res_err = yield user.bag_equip_mgr.equip_discard( camp_id, pos_id, old_ueid )

    #res_err = yield user.bag_equip_mgr.set_equip( set_type, camp_id, pos_id, old_ueid, new_ueid )
    defer.returnValue( res_err )



