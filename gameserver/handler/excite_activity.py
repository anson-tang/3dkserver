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
from system   import check_excite_activity_status, get_activity_notice_conf
from utils    import datetime2time

from twisted.internet import defer
from manager.gsuser   import g_UserMgr

from manager.gsexcite_activity import GSExciteActivityMgr
from models.newyear_package    import newYearPackage
from models.timelimited_shop   import timeLimitedShop

@route()
@defer.inlineCallbacks
def excite_activity_info(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    data = yield user.get_excite_activity_info()
    defer.returnValue( data )

@route()
@defer.inlineCallbacks
def refresh_mystical_shop(p, req):
    cid, [refresh_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)

    mystical_info = yield user.excite_activity_mgr.mystical_info( refresh_type )

    defer.returnValue( mystical_info )

@route()
def exchange_mystical_item(p, req):
    cid, [index, item_type, item_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    res_err = user.excite_activity_mgr.exchange_mystical_item( index, item_type, item_id )

    return res_err

@route()
@defer.inlineCallbacks
def daily_eat_peach(p, req):
    ''' 这里的返回值多了一层状态码
    '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.eat_peach()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_monthly_card_reward_new(p, req):
    ''' 领取月卡奖励 
    @card_type: 2-普通月卡, 3-双月卡
    @day_type: 1-今日的奖励, 2-昨日的奖励
    '''
    cid, [card_type, day_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    res_err = yield user.new_monthly_card_reward(card_type, day_type)

    defer.returnValue( res_err )

#@route()
#@defer.inlineCallbacks
#def get_monthly_card_reward(p, req):
#    ''' 这里的返回值多了一层状态码
#    '''
#    cid, = req
#
#    user = g_UserMgr.getUser(cid)
#    if not user:
#        log.error('Can not find user. cid: {0}.'.format( cid ))
#        defer.returnValue( CONNECTION_LOSE )
#
#    res_err = yield user.monthly_card_reward()
#
#    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def buy_growth_plan(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.buy_growth_plan()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_growth_plan_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.growth_plan_status()
 
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_growth_plan_reward(p, req):
    cid, [plan_level] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.growth_plan_reward( plan_level )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_grow_server_reward(p, req):
    cid, [buy_num] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.get_grow_plan_server_reward( buy_num )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_vip_welfare_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.vip_welfare_status()

    defer.returnValue( res_err )
@route()
@defer.inlineCallbacks
def get_vip_welfare_reward(p, req):
    cid, [t_type] =req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.vip_welfare_reward(t_type)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_exchange_limited_list(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 检查活动状态 1-开启或 0-关闭
    _status = check_excite_activity_status( EXCITE_EXCHANGE_LIMITED )
    if not _status:
        defer.returnValue( EXCITE_ACTIVITY_STOP_ERROR )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    res_err = yield user.excite_activity_mgr.exchange_limited_list()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def refresh_exchange_material(p, req):
    cid, ( exchange_id, ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 检查活动状态 1-开启或 0-关闭
    _status = check_excite_activity_status( EXCITE_EXCHANGE_LIMITED )
    if not _status:
        defer.returnValue( EXCITE_ACTIVITY_STOP_ERROR )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    res_err = yield user.excite_activity_mgr.exchange_limited_mgr.refresh_exchange_material( exchange_id )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def lock_exchange_material(p, req):
    cid, ( exchange_id, lock_type ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 检查活动状态 1-开启或 0-关闭
    _status = check_excite_activity_status( EXCITE_EXCHANGE_LIMITED )
    if not _status:
        defer.returnValue( EXCITE_ACTIVITY_STOP_ERROR )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    res_err = yield user.excite_activity_mgr.exchange_limited_mgr.lock_exchange_material( exchange_id, lock_type )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def exchange_limited(p, req):
    cid, ( exchange_id, ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    res_err = yield user.excite_activity_mgr.exchange_limited_mgr.do_exchange( exchange_id )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_limit_fellow_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)

    res_err = yield user.excite_activity_mgr.limit_fellow_mgr.limit_fellow_info()
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def limit_fellow_randcard(p, req):
    cid, [rand_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 检查活动状态 1-开启或 0-关闭
    _status = check_excite_activity_status( EXCITE_LIMIT_FELLOW )
    if not _status:
        defer.returnValue( EXCITE_ACTIVITY_STOP_ERROR )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)

    res_err = yield user.excite_activity_mgr.limit_fellow_mgr.randcard(rand_type)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_pay_activity_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.pay_activity_status()
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_pay_activity_award(p, req):
    cid, [award_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 检查活动状态 1-开启或 0-关闭
    _status = check_excite_activity_status( EXCITE_PAY_ACTIVITY )
    if not _status:
        defer.returnValue( EXCITE_ACTIVITY_STOP_ERROR )

    res_err = yield user.pay_activity_award(award_id)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_consume_activity_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.consume_activity_status()
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_consume_activity_award(p, req):
    cid, [award_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 检查活动状态 1-开启或 0-关闭
    _status = check_excite_activity_status( EXCITE_CONSUME_ACTIVITY )
    if not _status:
        defer.returnValue( EXCITE_ACTIVITY_STOP_ERROR )

    res_err = yield user.consume_activity_award(award_id)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_newyear_package(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res, item = yield newYearPackage.receive(user)
    if res:
        defer.returnValue( res )
    else:
        defer.returnValue( (item, newYearPackage.received_list) )

@route()
@defer.inlineCallbacks
def exchange_happynewyear_package(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    
    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    
    res = yield user.excite_activity_mgr.exchange_happy_new_year()
    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def dig_treasure_by_credits(p, req):
    cid, [t_type, count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    
    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)

    res = yield user.excite_activity_mgr.get_dig_treasure_reward(t_type, count) 
    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def time_limited_shop_list(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res = yield timeLimitedShop.shop_list(user)
    if res:
        defer.returnValue( res )
    else:
        defer.returnValue( TIME_LIMITED_SHOP_ALL_GROUP_CLOSED )

@route()
@defer.inlineCallbacks
def time_limited_shop_buy(p, req):
    cid, [shop_id_buy, buy_cnt] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if buy_cnt <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res, item = yield timeLimitedShop.buy(user, shop_id_buy, buy_cnt)
    if res:
        defer.returnValue( res )
    else:
        defer.returnValue( item )

@route()
@defer.inlineCallbacks
def get_group_buy_info(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    
    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    
    res = yield user.excite_activity_mgr.get_group_buy_info()
    defer.returnValue( res )


@route()
@defer.inlineCallbacks
def get_group_buy_package(p, req):
    cid, [buy_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    
    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    
    res = yield user.excite_activity_mgr.buy_group_package(buy_type)
    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def get_group_buy_package_reward(p, req):
    cid, [buy_type, buy_count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
 
    if buy_count <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    if not hasattr(user, 'excite_activity_mgr'):
        user.excite_activity_mgr = GSExciteActivityMgr(user)
    
    res = yield user.excite_activity_mgr.get_group_buy_reward(buy_type, buy_count)
    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def get_lucky_turntable_status(p, req):
    ''' 获取幸运转盘的基本信息 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
 
    res_err = yield user.lucky_turntable_status()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def lucky_turntable_item(p, req):
    ''' 幸运转盘中抽取幸运道具 '''
    cid, [turntable_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
 
    res_err = yield user.turntable_item(turntable_type)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def lucky_turntable_reward(p, req):
    ''' 幸运转盘中领取每日某个档位的首充奖励 '''
    cid, [turntable_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
 
    res_err = yield user.turntable_reward(turntable_type)

    defer.returnValue( res_err )

@route()
def activity_notice_info(p, req):
    ''' 获取活动公告的内容 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE
 
    notice_data = []
    notice_conf = get_activity_notice_conf()
    for _c in notice_conf.itervalues():
        notice_data.append( [_c['ID'], _c['Title'], _c['Content'], datetime2time(_c['OpenTime']), datetime2time(_c['CloseTime'])] )

    return notice_data



