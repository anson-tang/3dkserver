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
from system           import get_item_by_itemid, get_game_limit_value
from models.item      import *
from redis    import redis
from protocol_manager import alli_call, alli_send, ms_send
from models.arena     import g_ArenaMgr
from marshal import loads, dumps


@route()
@defer.inlineCallbacks
def item_list(p, req):
    res_err = UNKNOWN_ERROR

    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _len, value_list = yield user.bag_item_mgr.value_list
    max_capacity     = user.base_att.item_capacity
    defer.returnValue( (_len, max_capacity, value_list) )

@route()
@defer.inlineCallbacks
def item_use(p, req):
    res_err = UNKNOWN_ITEM_ERROR

    cid, [item_id, quantity] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    if quantity <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res_err = yield user.bag_item_mgr.item_use(item_id, quantity)

    defer.returnValue( res_err )


BAG_MANAGER_TYPE_EQUIP    = 1
BAG_MANAGER_TYPE_ITEM     = 5
BAG_MANAGER_TYPE_TREASURE = 6

@route()
@defer.inlineCallbacks
def item_sell(p, req):
    res_err = UNKNOWN_ITEM_ERROR

    cid, (user_item_ids, bag_type) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if bag_type == BAG_MANAGER_TYPE_EQUIP:
        res_err, _prices = yield user.bag_equip_mgr.get_sell_back_cost( user_item_ids )
        if not res_err:
            user.get_golds(_prices, WAY_SELL_EQUIP)
    elif bag_type == BAG_MANAGER_TYPE_ITEM:
        res_err, _prices = yield user.bag_item_mgr.get_sell_back_cost( user_item_ids )
        if not res_err:
            user.get_golds(_prices, WAY_SELL_ITEM)
    elif bag_type == BAG_MANAGER_TYPE_TREASURE:
        res_err, _prices = yield user.bag_treasure_mgr.get_sell_back_cost( user_item_ids )
        if not res_err:
            user.get_golds(_prices, WAY_SELL_TREASURE)
    else:
        res_err = UNKNOWN_BAG_TYPE
        defer.returnValue( res_err )

    if res_err:
        defer.returnValue( res_err )

    defer.returnValue( [user.golds] )

DIRECT_PACKAGE_ID = 4008
SEVEN_DAY = 4009
@route()
@defer.inlineCallbacks
def get_direct_package_reward(p, req):
    cid, [package_id, item_id, item_num] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if item_num <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    if package_id not in [ DIRECT_PACKAGE_ID, SEVEN_DAY]:
        defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
    totalnum, attrs = yield user.bag_item_mgr.get_items(package_id)
    if totalnum == 0:
        defer.returnValue(CHAR_ITEM_NOT_ENOUGH)
    res = yield item_use_normal_item(user, ItemType = ITEM_TYPE_DIRECT_PACKAGE, ItemID = package_id, ItemNum = 1)
    left_res = (res[1][0][0], res[1][0][1], res[1][0][2], res[1][0][3])
    if package_id == DIRECT_PACKAGE_ID:
        reward = yield item_add_normal_item(user, ItemType=ITEM_TYPE_DIRECT_PACKAGE, ItemID=item_id, ItemNum=item_num, AddType=WAY_DIRECT_PACKAGE)
    elif package_id == SEVEN_DAY:
        reward = yield item_add_fellow(user, ItemType=ITEM_TYPE_FELLOW, ItemID=item_id, ItemNum=item_num, AddType=WAY_DIRECT_PACKAGE)

    defer.returnValue(([left_res], reward[1]))

@route()
@defer.inlineCallbacks
def use_named_card(p, req):
    cid, [c_type, card_id, new_name] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    
    if c_type == 0 or c_type == 2:
        totalnum, attrs = yield user.bag_item_mgr.get_items(card_id)
        if totalnum == 0:
            defer.returnValue(CHAR_ITEM_NOT_ENOUGH)
    elif (c_type == 1 or c_type == 3 ) and card_id == 0:
        cost_credits = get_game_limit_value(16) if c_type == 1 else get_game_limit_value(17)
        if user.credits < cost_credits:
            defer.returnValue(CHAR_CREDIT_NOT_ENOUGH)
    else:
        defer.returnValue(NAMED_TYPE_IS_WRONG)

    left_res = []
    if c_type == 0 or c_type == 1:
        had_cid = yield redis.hget(DICT_NICKNAME_REGISTERED, new_name)
        if had_cid:
            defer.returnValue(NICK_NAME_IS_USED)
        if c_type == 0:
            res = yield item_use_normal_item(user, ItemType = ITEM_TYPE_ITEM, ItemID = card_id, ItemNum = 1)
            left_res = (res[1][0][0], res[1][0][1], res[1][0][2], res[1][0][3])
        else:
            yield user.consume_credits(cost_credits, WAY_TO_NAMED)

        yield redis.hdel(DICT_NICKNAME_REGISTERED, user.nick_name) 
        user.base_att.nick_name = new_name
        yield redis.hset(DICT_NICKNAME_REGISTERED, new_name, user.cid)
        #alliance
        _s = yield redis.hget(HASH_ALLIANCE_MEMBER, cid)
        if _s:
            _s = list(loads(_s))
            _s[1] = new_name
            yield redis.hset(HASH_ALLIANCE_MEMBER, cid, dumps(_s))
        alli_send('revise_member_name', [cid, new_name])
        #msg
        ms_send('revise_name', [cid, new_name])
        #arena
        _rank = yield g_ArenaMgr.get_char_rank(cid)
        _detail = yield redis.hget( HASH_ARENA_RANK, _rank)
        if _detail:
            _detail = loads(_detail)
            _detail[2] = new_name
            yield redis.hset( HASH_ARENA_RANK, _rank, dumps(_detail))
        
        alliance_info = yield alli_call('get_alliance_info', [cid])
        if alliance_info[0] != 0:
            if alliance_info[2] == ALLIANCE_POSITION_LEADER:
                res = yield alli_call('revise_leader', [user.alliance_id, new_name])

    elif c_type == 2 or c_type ==3:
        alliance_info = yield alli_call('get_alliance_info', [cid])
        if alliance_info[0] != 0:
            if alliance_info[2] != ALLIANCE_POSITION_LEADER:
                defer.returnValue(ALLIANCE_AUTHORITY_ERROR)
            res = yield alli_call('check_alliance_name', [new_name, user.alliance_id]) 
            user.alliance_name = new_name
            if res != 0:
                defer.returnValue(res)
            if c_type == 2:
                res = yield item_use_normal_item(user, ItemType = ITEM_TYPE_ITEM, ItemID = card_id, ItemNum = 1)
                left_res = (res[1][0][0], res[1][0][1], res[1][0][2], res[1][0][3])
            else:
                yield user.consume_credits(cost_credits, WAY_TO_NAMED)
        else:
            defer.returnValue(ALLIANCE_UNKNOWN_ERROR)
    else:
        defer.returnValue(NAMED_TYPE_IS_WRONG)

    defer.returnValue([left_res, user.credits])

