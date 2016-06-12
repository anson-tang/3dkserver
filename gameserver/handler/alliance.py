#!/usr/bin/env python
#-*-coding: utf-8-*-

from rpc              import route
from twisted.internet import defer

from log              import log
from errorno          import *
from constant         import *
from manager.gsuser   import g_UserMgr
from models.item      import *

TYPE_USE_GOLDS   = 1
TYPE_USE_CREDITS = 2


@route()
def gs_alliance_info(p, req):
    ''' 同步或更新玩家的公会ID '''
    cid, alliance_info = req

    user = g_UserMgr.getUser(cid)
    if user:
        user.alliance_id = alliance_info[0]
        user.alliance_name = alliance_info[1]

@route()
@defer.inlineCallbacks
def gs_create_alliance(p, req):
    '''
    '''
    cid, create_type = req

    res  = UNKNOWN_ERROR
    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( (CONNECTION_LOSE, 0, 0) )

    if create_type == TYPE_USE_GOLDS:
        res = user.consume_golds( ALLIANCE_CREATE_GOLDS, WAY_ALLIANCE_CREATE )
    elif create_type == TYPE_USE_CREDITS:
        res = yield user.consume_credits( ALLIANCE_CREATE_CREDITS, WAY_ALLIANCE_CREATE )

    defer.returnValue( (res, user.golds, user.credits) )

@route()
@defer.inlineCallbacks
def gs_alliance_hall_contribute(p, req):
    ''' 公会成员建设大殿,扣除金币或者钻石 '''
    cid, item_id, item_num = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( (CONNECTION_LOSE, 0, 0) )

    if item_id == ITEM_MONEY_GOLDS:
        res = user.consume_golds( item_num, WAY_ALLIANCE_HALL_CONTRIBUTE )
    elif item_id == ITEM_MONEY_CREDITS:
        res = yield user.consume_credits( item_num, WAY_ALLIANCE_HALL_CONTRIBUTE )

    defer.returnValue( (res, user.golds, user.credits) )

@route()
@defer.inlineCallbacks
def gs_alliance_sacrifice(p, req):
    ''' 公会成员拜祭女蜗宫 '''
    cid, need_credits, award_list = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( (CONNECTION_LOSE, 0, []) )

    res = yield user.consume_credits( need_credits, WAY_ALLIANCE_SACRIFICE )
    if res:
        defer.returnValue( (res, user.credits, []) )

    items_return = []
    for _type, _id, _num in award_list:
        model = ITEM_MODELs.get(_type, None)
        if not model:
            log.error('Unknown item type. item type: {0}.'.format( _type ))
            continue
        errorno, res_value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_ALLIANCE_SACRIFICE)
        if not errorno:
            for _v in res_value:
                items_return = total_new_items(_v, items_return)

    defer.returnValue( (NO_ERROR, user.credits, items_return) )

@route()
@defer.inlineCallbacks
def gs_exchange_item(p, req):
    ''' 公会商店 兑换道具 '''
    cid, add_type, items_list = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( (CONNECTION_LOSE, []) )

    items_return = []
    for _type, _id, _num in items_list:
        model = ITEM_MODELs.get(_type, None)
        if not model:
            log.error('Unknown item type. item type: {0}.'.format( _type ))
            continue
        errorno, res_value = yield model(user, ItemID=_id, ItemNum=_num, AddType=add_type)
        if not errorno:
            for _v in res_value:
                items_return = total_new_items(_v, items_return)

    defer.returnValue( (NO_ERROR, items_return) )


@route()
@defer.inlineCallbacks
def gs_update_achievement(p, req):
    cid, t_type, count = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )
    
    yield user.achievement_mgr.update_achievement_status(t_type, count)
    defer.returnValue(NO_ERROR)

