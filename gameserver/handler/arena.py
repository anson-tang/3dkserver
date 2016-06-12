#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import sys
from rpc      import route
from log      import log
from errorno  import *
from constant import *

from twisted.internet import defer
from manager.gsuser   import g_UserMgr
from models.arena     import g_ArenaMgr
from models.item      import ITEM_MODELs
from protocol_manager import gw_broadcast

@route()
@defer.inlineCallbacks
def get_arena_info(p, req):
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    arena_data = yield g_ArenaMgr.arena_info( user )

    defer.returnValue( arena_data )

@route()
@defer.inlineCallbacks
def get_arena_ranklist(p, req):
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    ranklist_data = yield g_ArenaMgr.ranklist()

    defer.returnValue( ranklist_data )

@route()
@defer.inlineCallbacks
def sync_arena_rank(p, req):
    ''' battle_status: 0:战斗失败; 1:战斗胜利
    '''
    res_err = UNKNOWN_ERROR

    cid, [my_rank, enemy_rank, battle_status] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    # 挑战的对手肯定有排名
    if (enemy_rank <= 0) or (my_rank == enemy_rank):
        log.error('client data error. req: {0}.'.format( req ))
        defer.returnValue( REQUEST_LIMIT_ERROR )

    items_list = yield g_ArenaMgr.lottery_items(user, my_rank, enemy_rank, battle_status)

    defer.returnValue( items_list )

@route()
@defer.inlineCallbacks
def get_arena_lucky_ranklist(p, req):
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    lucky_ranklist = yield g_ArenaMgr.lucky_ranklist()

    defer.returnValue( lucky_ranklist )

@route()
@defer.inlineCallbacks
def sync_arena_lottery(p, req):
    ''' 
    翻牌奖励进玩家背包 
    @param: msg_notice-0:无走马灯,1-走马灯广播'''
    res_err = UNKNOWN_ERROR
    cid, [item_type, item_id, item_num, msg_notice] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _model = ITEM_MODELs.get( item_type, None )
    if not _model:
        log.error('Unknown item type. item_type: {0}.'.format( item_type ))
        defer.returnValue( UNKNOWN_ITEM_ERROR )

    res_err, value = yield _model( user, ItemID=item_id, ItemNum=item_num, AddType=WAY_LOTTERY_AWARD, CapacityFlag=False )
    if res_err:
        defer.returnValue( res_err )

    # 翻牌得到稀有道具
    if msg_notice:
        message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_LOTTERY, [user.base_att.nick_name, item_type, item_id, item_num]]]
        gw_broadcast('sync_broadcast', [message])

    defer.returnValue( value )

@route()
@defer.inlineCallbacks
def prestige_exchange_status(p, req):
    '''
    @summary: 获取竞技场 声望兑换中玩家的状态信息
    '''
    res_err = UNKNOWN_ERROR
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _status = yield g_ArenaMgr.exchange_status( cid )
    defer.returnValue( _status )

@route()
@defer.inlineCallbacks
def prestige_exchange(p, req):
    '''
    @summary: 竞技场 声望兑换
    '''
    res_err = UNKNOWN_ERROR
    cid, [exchange_id, exchange_count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    if exchange_count <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res_err = yield g_ArenaMgr.exchange( user, exchange_id, exchange_count )

    defer.returnValue( res_err )


