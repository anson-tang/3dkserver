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
from manager.user         import g_UserMgr
from server               import server
from redis                import redis



@route()
@defer.inlineCallbacks
def sync_char_data(p, req):
    ''' _type: 1-nick_name, 2-lead_id, 3-vip_level, 4-level, 5-might '''
    cid, _type, _value = req

    user = g_UserMgr.getUser(cid)
    if user:
        if _type == SYNC_NICK_NAME:
            user.rename( _value )
        elif _type == SYNC_LEAD_ID:
            user.update_lead_id( _value )
        elif _type == SYNC_LEVEL:
            user.update_level( _value )
        elif _type == SYNC_MIGHT:
            yield user.update_might( _value )
        elif _type == SYNC_ARENA_RANK:
            user.update_arena_rank( _value )
        elif _type == SYNC_VIP_LEVEL:
            user.update_vip_level( _value )

@route()
@defer.inlineCallbacks
def get_alliance_info(p, req):
    cid, = req

    alliance_info = 0, '', 0

    user = yield g_UserMgr.get_offline_user(cid)
    if (not user) or (not user.alliance):
        defer.returnValue( alliance_info )

    alliance_info = user.alliance.aid, user.alliance.name, user.position

    defer.returnValue( alliance_info )

@route()
def get_alliance_names(p, req):
    ''' 通过工会ID获取公会名称 '''
    alliance_ids, = req

    alliance_names = []
    for _a_id in alliance_ids:
        _a = server.get_alliance( _a_id )
        if _a:
            alliance_names.append( (_a_id, _a.name) )
        else:
            alliance_names.append((_a_id, ''))

    return alliance_names

@route()
@defer.inlineCallbacks
def check_alliance_name(p, req):
    alliance_name, alliance_id = req
    _all = server.alliances
    for _alliance in _all:
        if _alliance.name == alliance_name:
            defer.returnValue(ALLIANCE_NAME_DUPLICATED)
    _a = server.get_alliance(alliance_id)
    if _a:
        _a.revise_name(alliance_name)
        yield redis.hset( HASH_ALLIANCE_INFO, _a.aid, _a.stream )
    else:
        defer.returnValue (ALLIANCE_UNKNOWN_ERROR)
    defer.returnValue(0)

@route()
@defer.inlineCallbacks
def revise_leader(p, req):
    alliance_id, leader_name = req
    
    _a = server.get_alliance(alliance_id)
    if _a:
        _a.revise_leader_name(leader_name)
        yield redis.hset( HASH_ALLIANCE_INFO, _a.aid, _a.stream )
    else:
        defer.returnValue (ALLIANCE_UNKNOWN_ERROR)
    defer.returnValue(0)

@route()
def revise_member_name(p, req):
    cid, new_name = req
    
    user = g_UserMgr.getUser(cid)
    if user:
        user.rename(new_name)
