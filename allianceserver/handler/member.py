#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time     import time
from rpc      import route
from log      import log
from errorno  import *
from constant import *

from twisted.internet import defer
from manager.user     import g_UserMgr
from manager.request  import Request, character_requests
from server           import server

@route()
def alliance_request_list( p, req ):
    ''' 获取自己已申请的公会列表 '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE
 
    if _m.alliance:
        return ALLIANCE_SELF_HAD_IN

    _info = [ _r.aid for _r in character_requests( cid ) if _r.aid >= 0 ]
    return _info

@route()
@defer.inlineCallbacks
def alliance_join_request( p, req ):
    ''' 申请/取消申请加入公会 '''
    cid, [alliance_id, req_type] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        defer.returnValue( CONNECTION_LOSE )

    if _m.alliance:
        defer.returnValue( ALLIANCE_SELF_HAD_IN )

    if _m.cd_time > int(time()):
        defer.returnValue( IN_COOLDOWN_ERROR )

    _reqs = character_requests( cid )

    _alliance = server.get_alliance( alliance_id )
    # 该公会不存在
    if not _alliance:
        defer.returnValue( ALLIANCE_UNKNOWN_ERROR )

    res_err = UNKNOWN_ERROR
    if req_type == 1: # 申请加入公会
        if len(_reqs) >= ALLIANCE_REQUEST_MAX: 
            defer.returnValue( ALLIANCE_APPLY_COUNT_ERROR )
        res_err = _alliance.new_request( _m )
    elif req_type == 2: # 取消申请
        res_err = yield _alliance.del_request( _m.cid )

    defer.returnValue( res_err )

@route()
def alliance_join_audit_list(p, req):
    ''' 会长/副会长 获取加入公会的申请列表 '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE

    if not _m.alliance or not _m.has_authority:
        return ALLIANCE_NEED_VICE_LEADER

    _info = _m.alliance.request_info()
    return _info

@route()
@defer.inlineCallbacks
def alliance_join_audit(p, req):
    ''' 审核公会申请 '''
    cid, [_type, req_cid] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        defer.returnValue( CONNECTION_LOSE )

    if not _m.alliance or not _m.has_authority:
        defer.returnValue( ALLIANCE_NEED_VICE_LEADER )

    if _type == ALLIANCE_REQUEST_REJECT:
        if not req_cid:
            res_err = yield _m.alliance.reject_all()
        else:
            res_err = yield _m.alliance.del_request( req_cid )
    else:
        res_err = yield _m.alliance.del_request( req_cid, True, _m )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def alliance_leave(p, req):
    ''' 离开公会 '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        defer.returnValue( CONNECTION_LOSE )

    if not _m.alliance:
        defer.returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    if _m.isLeader:
        defer.returnValue( ALLIANCE_LEADER_LEAVE_ERROR )

    _alliance = server.get_alliance( _m.alliance.aid )
    if not _alliance:
        defer.returnValue( ALLIANCE_UNKNOWN_ERROR )

    yield _alliance.del_member( _m )
    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def alliance_kick(p, req):
    ''' 将成员踢出公会 '''
    cid, [kick_cid] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        defer.returnValue( CONNECTION_LOSE )

    if not _m.alliance or not _m.has_authority:
        defer.returnValue( ALLIANCE_NEED_VICE_LEADER )

    _kick_m = yield g_UserMgr.get_offline_user( kick_cid )
    if not _kick_m:
        defer.returnValue( UNKNOWN_ERROR )

    # 判断该玩家当前的公会状态    
    if not _kick_m.alliance or _kick_m.alliance.aid != _m.alliance.aid:
        _m.alliance.del_invalid_member( _kick_m )
        defer.returnValue( NO_ERROR )

    if _kick_m.position and _m.position >= _kick_m.position:
        defer.returnValue( ALLIANCE_NEED_VICE_LEADER )

    yield _m.alliance.del_member( _kick_m, _m )
    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def alliance_appoint(p, req):
    ''' 公会任命 '''
    cid, [other_cid, position] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        defer.returnValue( CONNECTION_LOSE )

    if not _m.alliance or not _m.has_authority:
        defer.returnValue( ALLIANCE_NEED_VICE_LEADER )

    # 判断该玩家当前的公会状态    
    _other_m = yield g_UserMgr.get_offline_user( other_cid )
    if not _other_m or not _other_m.alliance or _other_m.alliance.aid != _m.alliance.aid:
        defer.returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    if _other_m.position == position:
        defer.returnValue( ALLIANCE_HAD_IN_POSITION )

    if position == ALLIANCE_POSITION_LEADER:
        if _m.isLeader:
            _m.update_position( ALLIANCE_POSITION_NORMAL )
            res_err = _m.alliance.appoint_leader( _other_m, _m )
            defer.returnValue( res_err )
        else:
            defer.returnValue( ALLIANCE_NEED_LEADER )
    elif position == ALLIANCE_POSITION_VICE:
        if not _m.isLeader:
            defer.returnValue( ALLIANCE_NEED_LEADER )

        res_err = _m.alliance.appoint_vice( _other_m, _m )
        defer.returnValue( res_err )
    else:
        res_err = _m.alliance.appoint_normal( _other_m, _m )
        defer.returnValue( res_err )





