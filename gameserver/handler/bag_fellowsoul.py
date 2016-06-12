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
from system           import get_expand_bag_by_bagtype, get_fellow_by_fid
from manager.gsuser   import g_UserMgr

@route()
@defer.inlineCallbacks
def fellowsoul_list(p, req):
    res_err = UNKNOWN_ERROR
    
    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _len, value_list = yield user.bag_fellowsoul_mgr.value_list
    defer.returnValue( (_len, value_list) )

@route()
@defer.inlineCallbacks
def fellowsoul_combine(p, req):
    res_err = UNKNOWN_ERROR

    cid, [user_fellow_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err, fellow_id = yield user.bag_fellowsoul_mgr.combine( user_fellow_id )
    if not res_err:
        try:
            # args: fellow_id, is_major, camp_id, on_troop
            res_err, attrib = yield user.fellow_mgr.create_table_data( fellow_id, 0, 0, 0 )
        except Exception as e:
            log.warn('Create fellow fail! e:', e)
            defer.returnValue(res_err)
        #errorno, value = yield user.fellow_mgr.addNewFellow( fellow_id )
        if not res_err:
            _conf = get_fellow_by_fid(fellow_id)
            if _conf:
                q = _conf.get('Quality', 0)
                if q>= 2:
                    user.achievement_mgr.update_achievement_status(29, 1)
                if q>= 3:
                    user.achievement_mgr.update_achievement_status(30, 1)
                if q>= 4:
                    user.achievement_mgr.update_achievement_status(31, 1)
            defer.returnValue( [attrib.attrib_id, attrib.fellow_id] )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def expand_bag(p, req):
    res_err = UNKNOWN_ERROR

    cid, [bag_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if bag_type < 1 or bag_type > len(BAG_TYPE_CAPACITY):
        log.error('expand_bag. Bag type error.')
        defer.returnValue( res_err )
    next_capacity = 10000
    next_bag      = {}
    cur_capacity  = user.base_att_value[BAG_TYPE_CAPACITY[bag_type]]
    bag_data      = get_expand_bag_by_bagtype( bag_type )
    for _bag in bag_data:
        if next_capacity > _bag['BagCount'] and _bag['BagCount'] > cur_capacity:
            next_capacity = _bag['BagCount']
            next_bag      = _bag

    if not next_bag:
        log.error('expand_bag. Bag has max capacity.')
        defer.returnValue( res_err )

    if user.base_att.credits < next_bag['Cost']:
        log.error("expand_bag. User's credits not enough. ")
        defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )

    if next_bag['Cost']:
        yield user.consume_credits( next_bag['Cost'], WAY_BAG_EXPAND )
    #user.base_att.credits        -= next_bag['Cost']
    user.expand_bag(bag_type, next_bag['BagCount'])

    defer.returnValue( (bag_type, next_bag['BagCount'], user.base_att.credits) )



