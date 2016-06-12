#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from log      import log
from time     import time
from rpc      import route
from errorno  import *
from constant import *

from twisted.internet    import defer
from manager.gsuser      import g_UserMgr
from manager.gscharacter import GSCharacter
from manager.gsshop      import GSRandCardMgr, VipPackageMgr
from protocol_manager    import cs_call


@route()
@defer.inlineCallbacks
def randcard_status(p, req):
    '''
    @summary: 获取抽卡的状态信息
    '''
    res_err = UNKNOWN_ERROR

    cid, = req
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    randcard_mgr = GSRandCardMgr( user )
    res_err = yield randcard_mgr.status()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def randcard_status_new(p, req):
    '''
    @summary: 获取抽卡的状态信息 客户端版本v0.3.3.2以后使用
    '''
    cid, = req
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    randcard_mgr = GSRandCardMgr( user )
    res_err = yield randcard_mgr.status(True)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def randcard(p, req):
    '''
    @summary: In client, card_type=1 ~ 3
    '''
    res_err = UNKNOWN_ERROR

    cid, (card_type, rand_times) = req
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    # 背包容量判断 (去掉容量判断)
    #cur_capacity = yield user.fellow_mgr.cur_capacity()
    #if cur_capacity >= user.base_att.fellow_capacity:
    #    log.error('cid: {0}, max fellow capacity: {1}, cur_capacity: {2}.'.format( cid, user.base_att.fellow_capacity, cur_capacity ))
    #    defer.returnValue( FELLOW_CAPACITY_NOT_ENOUGH )

    if rand_times <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    randcard_mgr = GSRandCardMgr( user )
    res_err = yield randcard_mgr.randcard( card_type, rand_times )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def camp_randcard(p, req):
    '''
    @summary: In client, camp_id=1 ~ 6
    '''
    cid, [camp_id] = req
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    randcard_mgr = GSRandCardMgr( user )
    res_err = yield randcard_mgr.camp_randcard( camp_id )

    defer.returnValue( res_err )

@route()
def buyed_shop_item(p, req):
    '''
    @summary: 道具商店中的道具每日已购买的数量, 并于每日6点清零
    '''
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return res_err

    return user.get_buyed_item()

@route()
@defer.inlineCallbacks
def buy_shop_item(p, req):
    '''
    @summary: 在道具商店中购买道具
    '''
    res_err = UNKNOWN_ERROR

    cid, [shop_item_id, item_num]= req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    if item_num <= 0:
        log.error('buy item num: {0}.'.format( item_num ))
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res_err = yield user.buy_item( shop_item_id, item_num )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def buyed_vip_package(p, req):
    '''
    @summary: 获取在VIP礼包商店中的已购买的VIP等级礼包
    '''
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _data = yield VipPackageMgr.buyed_package( cid )
    defer.returnValue( _data )

@route()
@defer.inlineCallbacks
def buy_vip_package(p, req):
    '''
    @summary: 购买VIP礼包
    '''
    res_err = UNKNOWN_ERROR

    cid, [vip_level] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield VipPackageMgr.buy_package(user, vip_level)

    defer.returnValue( res_err )

