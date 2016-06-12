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
def treasure_list(p, req):
    res_err = UNKNOWN_ERROR

    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _len, value_list = yield user.bag_treasure_mgr.value_list
    max_capacity     = user.base_att.treasure_capacity
    defer.returnValue( (_len, max_capacity, value_list) )

@route()
@defer.inlineCallbacks
def treasure_strengthen(p, req):
    res_err = UNKNOWN_ERROR

    cid, [user_treasure_id, treasures_data] = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    if (not treasures_data) or len(treasures_data) > 5:
        log.error('No one treasure to be selected. treasures_data: {0}.'.format( treasures_data ))
        defer.returnValue( res_err )

    res_err = yield user.bag_treasure_mgr.strengthen(user_treasure_id, treasures_data)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def treasure_refine(p, req):
    res_err = UNKNOWN_ERROR

    cid, [user_treasure_id] = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.bag_treasure_mgr.refine(user_treasure_id)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_camp_treasure(p, req):
    res_err = UNKNOWN_ERROR

    cid, [camp_id, pos_id, old_ueid, new_ueid] = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    # 玩家装备ID不能同时为空
    if not (old_ueid or new_ueid):
        log.error('set treasure error. old_ueid and new_ueid could not be all null.')
        defer.returnValue( CLIENT_DATA_ERROR )
    elif old_ueid and new_ueid: # 更换
        res_err = yield user.bag_treasure_mgr.treasure_replace( camp_id, pos_id, old_ueid, new_ueid )
    elif new_ueid: # 新增
        res_err = yield user.bag_treasure_mgr.treasure_wear( camp_id, pos_id, new_ueid )
    else: # 卸下
        res_err = yield user.bag_treasure_mgr.treasure_discard( camp_id, pos_id, old_ueid )

    defer.returnValue( res_err )


