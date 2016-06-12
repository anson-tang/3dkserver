#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: all alliance protocol need start by alliance.
#

from rpc      import route
from log      import log
from errorno  import *
from constant import *

from twisted.internet.defer import inlineCallbacks, returnValue
from protocol_manager       import protocol_manager, gs_call
from manager.user           import g_UserMgr
from server                 import server
from syslogger              import syslogger


@route()
def alliance_info(p, req):
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE

    _info = None
    _alliance = _m.alliance
    if _alliance:
        _rank = server.rank( _alliance )
        _info = _alliance.info + [ _rank, _alliance.building_levels, _alliance.notice ]
    else:
        _info = []

    return (_m.cd_time, _m.contribution, _m.position, _info)

@route()
def alliance_list(p, req):
    cid, [index,] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE

    _all   = server.alliances
    _total = len(_all)
    _start = _total - index - ALLIANCES_PER_PAGE
    _start = _start if _start > 0 else 0
    #_end   = _total - index
    _list = _all[_start:]
    _list.reverse()

    _alliances = []
    for _i, _alliance in enumerate(_list):
        #_rank  = server.rank( _alliance )
        _rank = _i + 1
        _alliances.append( _alliance.info + [ _rank ] )

    return [index, len(_all), _alliances]

@route()
def alliance_search(p, req):
    cid, [name, index] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE

    _all   = server.filter_by_name( name )

    _list = _all[:index + ALLIANCES_PER_PAGE]
    _alliances = []

    for _alliance in _list:
        _rank  = server.rank( _alliance )
        _alliances.append( _alliance.info + [ _rank ] )

    return [index, len(_all), _alliances]

@route()
@inlineCallbacks
def alliance_create(p, req):
    cid, [ name, create_type ] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 判断玩家是否有仙盟
    if _m.alliance:
        returnValue( ALLIANCE_SELF_HAD_IN )

    name = name.strip()

    _all = server.alliances
    for _alliance in _all:
        # 仙盟名重复
        if _alliance.name == name:
            returnValue( ALLIANCE_NAME_DUPLICATED )

    res_gs, golds, credits = yield gs_call( 'gs_create_alliance', [ cid, create_type ] )
    if res_gs:
        returnValue( res_gs )

    _alliance = yield server.create_alliance( name, _m )
    _rank  = server.rank( _alliance )
    syslogger(LOG_ALLIANCE_CREATE, cid, _m.level, _m.vip_level, _alliance.aid)
    returnValue( (golds, credits, _alliance.info+[_rank, _alliance.notice]) )

@route()
@inlineCallbacks
def alliance_members(p, req):
    ''' 成员列表顺序由客户端排序 '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )

    if not _m.alliance:
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    _info = yield g_UserMgr.get_alliance_members( _m.alliance.members )
    returnValue( _info )

@route()
@inlineCallbacks
def alliance_dissolve(p, req):
    ''' 解散仙盟 '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )

    if not _m.alliance:
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    if not _m.isLeader:
        returnValue( ALLIANCE_NEED_LEADER )

    res_err = yield server.dissolve_alliance( _m.alliance.aid )
    if not res_err:
        syslogger(LOG_ALLIANCE_DISSOLVE, cid, _m.level, _m.vip_level, _m.alliance.aid)
        yield _m.clean_alliance()

    returnValue( res_err )

@route()
def alliance_modify_content(p, req):
    ''' 修改仙盟宣言/公告 '''
    cid, [desc_type, new_desc] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE
    # 操作权限检查
    if (not _m.alliance) or ((not _m.isLeader) and (not _m.isViceLeader)):
        return ALLIANCE_NEED_VICE_LEADER
    ## 长度限制
    #_length = len(new_desc)
    #if _length > 25:
    #    return STRING_LENGTH_ERROR

    _m.alliance.update_description(desc_type, new_desc)

    return NO_ERROR


@route()
@inlineCallbacks
def alliance_upgrade(p, req):
    ''' 建筑升级 
    '''
    cid, [build_type] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 操作权限检查
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )
    if((not _m.isLeader) and (not _m.isViceLeader)):
        returnValue( ALLIANCE_NEED_VICE_LEADER )

    res_err = yield _m.alliance.upgrade_level(_m, build_type)

    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_hall_info(p, req):
    ''' 仙盟大殿的建设信息
    '''
    cid, = req
 
    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.hall_info( cid )
    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_hall_contribute(p, req):
    ''' 仙盟成员建设仙盟大殿
    '''
    cid, [contribute_id] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.hall_contribute( contribute_id, _m )
    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_sacrifice_info(p, req):
    ''' 仙盟女娲宫基本信息
    '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.sacrifice_info( _m )
    if isinstance(res_err, (tuple, list)):
        returnValue( res_err[:5] )
    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_sacrifice(p, req):
    ''' 仙盟女蜗宫拜祭
    '''
    cid, [sacrifice_type] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.daily_sacrifice( sacrifice_type, _m )
    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_shop_limit_item_info(p, req):
    ''' 获取仙盟商店中珍宝的可兑换信息
    '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.limit_item_info(_m)

    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_shop_limit_item_exchange(p, req):
    ''' 兑换仙盟商店中的珍宝
    '''
    cid, [index] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.limit_item_exchange(_m, index)

    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_shop_item_info(p, req):
    ''' 获取仙盟商店中道具的可兑换信息
    '''
    cid, = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.item_info(_m)

    returnValue( res_err[1:] )

@route()
@inlineCallbacks
def alliance_shop_item_exchange(p, req):
    ''' 兑换仙盟商店中的道具
    '''
    cid, [shop_item_id] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.item_exchange(_m, shop_item_id)

    returnValue( res_err )

@route()
def alliance_action(p, req):
    cid, [index] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        return CONNECTION_LOSE
    # 仙盟成员判断
    if (not _m.alliance):
        return ALLIANCE_NOT_MEMBER_ERROR

    res_err = _m.alliance.get_all_actions( index )

    return res_err

@route()
@inlineCallbacks
def alliance_get_messages(p, req):
    ''' 获取留言 '''
    cid, [index] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.get_all_messages( _m, index )

    returnValue( res_err )

@route()
@inlineCallbacks
def alliance_add_messages(p, req):
    ''' 新增留言 '''
    cid, [content] = req

    _m = g_UserMgr.getUser( cid )
    if not _m:
        returnValue( CONNECTION_LOSE )
    # 仙盟成员判断
    if (not _m.alliance):
        returnValue( ALLIANCE_NOT_MEMBER_ERROR )

    res_err = yield _m.alliance.new_messages( _m, content )

    returnValue( res_err )


