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
from redis    import redis

from twisted.internet     import defer
from manager.messageuser  import g_UserMgr
from manager.channel      import g_Channel, Alliance
from manager.private      import g_Private
from protocol_manager     import gw_send



@route()
@defer.inlineCallbacks
def chat_channel(p, req):
    ''' 群聊 '''
    cid, [msg] = req

    _status = yield check_character_mute(int(cid))
    if _status:
        defer.returnValue( CHAR_IN_MUTE )

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = g_Channel.new_msg( user, msg )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def chat_private(p, req):
    ''' 私聊 '''
    cid, [rcv_nick_name, content] = req

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    _status = yield check_character_mute(int(cid))
    if _status:
        defer.returnValue( CHAR_IN_MUTE )

    rcv_cid = yield redis.hget(DICT_NICKNAME_REGISTERED, rcv_nick_name)
    if not rcv_cid:
        log.error('Can not find user. sender_id: {0}, rcv_cid: {1}, rcv_nick_name: {2}.'.format( cid, rcv_cid, rcv_nick_name ))
        defer.returnValue( UNKNOWN_CHAR )

    if rcv_cid == cid:
        defer.returnValue( UNKNOWN_ERROR )

    rcv_user = g_UserMgr.getUserByCid( rcv_cid )
    if not rcv_user:
        log.error('The user had not online. sender_id: {0}, rcv_cid: {1}.'.format( cid, rcv_cid ))
        defer.returnValue( CHAR_NOT_ONLINE )

    res_err = g_Private.new_msg( user, rcv_user, content )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def chat_alliance(p, req):
    ''' 公会聊天 '''
    cid, [msg] = req

    _status = yield check_character_mute(int(cid))
    if _status:
        defer.returnValue( CHAR_IN_MUTE ) 

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    if user.alliance_id < 1:
        defer.returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    _alliance = g_UserMgr.getAlliance( user.alliance_id )
    if not _alliance:
        _alliance = Alliance( user.alliance_id )
        g_UserMgr.addAlliance( _alliance )
    res_err = _alliance.new_msg( user, msg )

    defer.returnValue( res_err )

@route()
def chat_room_join(p, req):
    ''' 玩家进入房间, 返回20条记录 '''
    cid, [room_type] = req

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    res_err = []
    user.in_room = True
    if room_type == 1:
        res_err = g_Channel.last_msgs()
    elif room_type == 2:
        res_err = g_Private.last_msgs( cid )
    elif room_type == 3:
        if user.alliance_id < 1:
            return ALLIANCE_NOT_MEMBER_ERROR
        _alliance = g_UserMgr.getAlliance( user.alliance_id )
        if not _alliance:
            _alliance = Alliance( user.alliance_id )
            g_UserMgr.addAlliance( _alliance )
        res_err = _alliance.last_msgs()

    return res_err[-20:]

@route()
def chat_room_history(p, req):
    ''' 玩家获取历史聊天记录 '''
    cid, [room_type] = req

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    res_err = []
    if room_type == 1:
        res_err = g_Channel.last_msgs()
    elif room_type == 2:
        res_err = g_Private.last_msgs( cid )
    elif room_type == 3:
        if user.alliance_id < 1:
            return ALLIANCE_NOT_MEMBER_ERROR
        _alliance = g_UserMgr.getAlliance( user.alliance_id )
        if not _alliance:
            _alliance = Alliance( user.alliance_id )
            g_UserMgr.addAlliance( _alliance )
        res_err = _alliance.last_msgs()

    return res_err

@route()
def chat_room_leave(p, req):
    ''' 玩家退出房间 '''
    cid, = req

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    user.in_room     = False
    user.notice_flag = False

    return NO_ERROR

@defer.inlineCallbacks
def check_character_mute(cid):
    ''' return 0-未禁言, 1-禁言中
    '''
    _status   = 0
    _time_now = int(time())

    _end_timestamp = yield redis.hget(HASH_SERVER_MUTE, cid)
    if _end_timestamp is None:
        pass
    elif _end_timestamp < 0:
        _status = 1
    elif _end_timestamp > _time_now:
        _status = 1
    else:
        yield redis.hdel(HASH_SERVER_MUTE, cid)

    defer.returnValue( _status )


