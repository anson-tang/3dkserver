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
from redis    import redis

from syslogger        import syslogger
from twisted.internet import reactor, defer
from system           import get_item_by_itemid, get_vip_conf
from manager.gsuser   import g_UserMgr
from models.avoidwar  import AvoidWarMgr
from models.activity  import random_lottery_items
from models.item      import add_new_items, total_new_items, ITEM_MODELs

from protocol_manager  import ms_send
from handler.character import gs_offline_login, gs_offline_logout



@route()
@defer.inlineCallbacks
def get_plunder_info(p, req):
    '''
    @summary: 获取夺宝基本信息
    '''
    res_err = UNKNOWN_ERROR

    cid, (plunder_type, ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    shard_type = 0
    if plunder_type == 1: #战马
        shard_type = ITEM_TYPE_HORSESHARD
    elif plunder_type == 2: #兵书
        shard_type = ITEM_TYPE_BOOKWARSHARD
    else:
        log.error('[ get_plunder_info ]cid:{0}, Unknown plunder type: {1}.'.format( cid, plunder_type ))
        defer.returnValue( res_err )

    value_list = yield user.bag_treasureshard_mgr.value_list_by_type(shard_type)
    avoid_time = yield AvoidWarMgr.remain_avoid_war_time(cid)
    defer.returnValue( (avoid_time, value_list) )

@route()
@defer.inlineCallbacks
def avoid_war(p, req):
    '''
    @summary: 免战
    '''
    res_err = UNKNOWN_ERROR

    cid, (avoid_type, ) = req

    user = g_UserMgr.getUser(cid)
    if not user :
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _remain = 0
    items_return = []

    if avoid_type == 1: #使用免战牌
        total_num, item_attribs = yield user.bag_item_mgr.get_items( ITEM_AVOID_WAR_ID )
        if total_num == 0:
            defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
        else:
            res_err, used_attribs = yield user.bag_item_mgr.use( ITEM_AVOID_WAR_ID, 1 )
            if res_err:
                defer.returnValue( res_err )
            else:
                _remain = yield AvoidWarMgr.inc_avoid_war_time( cid )
                # used_attribs-已使用的道具
                for _a in used_attribs:
                    items_return.append( [_a.attrib_id, ITEM_TYPE_ITEM, ITEM_AVOID_WAR_ID, _a.item_num] )
                    # add syslog
                    syslogger(LOG_ITEM_LOSE, cid, user.level, user.vip_level, user.alliance_id, _a.attrib_id, ITEM_AVOID_WAR_ID, 1, WAY_AVOID_WAR)
    elif avoid_type == 2: #直接使用点卷
        _cost = AVOID_WAR_CREDITS
        if _cost > user.base_att.credits:
            log.error('credits. _cost: {0}, cur: {1}.'.format( _cost, user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        else:
            yield user.consume_credits( _cost, WAY_AVOID_WAR )
            _remain = yield AvoidWarMgr.inc_avoid_war_time( cid )

    defer.returnValue( (_remain, user.base_att.credits, items_return) )

@route()
@defer.inlineCallbacks
def avoid_player_list(p, req):
    '''
    @summary: 获取抢夺列表
    '''
    res_err = UNKNOWN_ERROR

    cid, (shard_id, ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    else:
        player_list = yield AvoidWarMgr.users_got_shards( shard_id, user.level, cid )
        defer.returnValue( player_list )

@route()
def start_plunder(p, req):
    '''
    @summary: 开始抢夺玩家, 避免同一宝物的碎片玩家被多人同时抢夺
    '''
    res_err = UNKNOWN_ERROR
    cid, ( plunder_cid, shard_id ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return res_err

    if user.base_att.douzhan < PVP_NEED_DOUZHAN:
        log.error('douzhan of user {0} have been zero!!!'.format( cid ))
        return CHAR_DOUZHAN_NOT_ENOUGH

    # 抢夺对象不是玩家
    if plunder_cid <= 0:
        return NO_ERROR

    item_conf = get_item_by_itemid( shard_id )
    if not item_conf:
        log.error('Can not find conf. shard_id: {0}.'.format( shard_id ))
        return NOT_FOUND_CONF

    # 碎片可合成的宝物信息
    _, treasure_id, _ = item_conf['ChangeList'][0]
    res_err = AvoidWarMgr.start_plunder_shard( treasure_id, plunder_cid )
    return res_err

@route()
@defer.inlineCallbacks
def plunder(p, req):
    '''
    @summary: 夺宝结算
    '''
    res_err = UNKNOWN_ERROR

    cid, ( plunder_cid, shard_id, won ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    if user.base_att.douzhan < PVP_NEED_DOUZHAN:
        log.error('douzhan of user {0} have been zero!!!'.format( cid ))
        defer.returnValue( CHAR_DOUZHAN_NOT_ENOUGH )

    item_conf = get_item_by_itemid( shard_id )
    treasure_id = 0
    if item_conf:
        _, treasure_id, _ = item_conf['ChangeList'][0]

    response = [0, 0, [], []]

    # 对玩家进行抢夺，免战自动解除
    if plunder_cid > 0: # 玩家
        yield redis.hdel( HASH_AVOID_WAR_TIME, cid )
        AvoidWarMgr.stop_plunder_shard( treasure_id, plunder_cid )
        _user_plundered = yield gs_offline_login( plunder_cid )
        if _user_plundered:
            reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, plunder_cid)
    else:
        _user_plundered = None

    if won:
        response[3] = yield random_lottery_items( cid, user.level, user.base_att.vip_level )
        err, add_items = yield AvoidWarMgr.rand_shard( user, shard_id, plunder_cid )

        if not err and (len(add_items) > 0): #抢到
            response[0] = 1
            response[2] = add_items[0][0], add_items[0][2]
            syslogger(LOG_AVOID_WAR, cid, user.level, user.vip_level, user.alliance_id, 0, won, add_items[0][0],add_items[0][2])
            if _user_plundered:
                ms_send('write_mail', (plunder_cid, MAIL_PAGE_BATTLE, MAIL_BATTLE_7, [user.lead_id, user.nick_name, shard_id]))
                yield _user_plundered.bag_treasureshard_mgr.dec_shard( shard_id )
            else:
                log.warn('No user be plundered. cid: {0}, plunder_cid: {1}.'.format( cid, plunder_cid ))
        else: # 未抢到
            response[0] = 0
            syslogger(LOG_AVOID_WAR, cid, user.level, user.vip_level, user.alliance_id, 0, won, 0, 0)
    else: # 战斗输了
        if _user_plundered:
            syslogger(LOG_AVOID_WAR, cid, user.level, user.vip_level, user.alliance_id, 0, won, 0, 0)
            ms_send('write_mail', (plunder_cid, MAIL_PAGE_BATTLE, MAIL_BATTLE_6, [user.lead_id, user.nick_name, shard_id]))
 
    if user.base_att.douzhan >= PVP_NEED_DOUZHAN:
        user.base_att.douzhan -= PVP_NEED_DOUZHAN
    # 每日任务计数
    yield user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_5, 1 )
    # 开服七天
    yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_8, 1)
    yield user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_8, 1)

    response[1] = user.base_att.douzhan

    defer.returnValue( response )

@route()
@defer.inlineCallbacks
def plunder_streak(p, req):
    '''
    @summary: 连续10次抢夺机器人, 非玩家
    '''
    res_err = UNKNOWN_ERROR

    cid, [plunder_cid, shard_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    # 等级限制 或者 VIP等级开关
    vip_conf = get_vip_conf( user.vip_level )
    res_err  = user.check_function_open(FUNCTION_TEN_PLUNDER)
    if res_err and (not vip_conf.get('TreasureTenPlunder', 0)):
        log.error('cid:{0}, level:{1}, vip_level:{2}.'.format( cid, user.level, user.vip_level ))
        defer.returnValue( CHAR_VIP_LEVEL_LIMIT )

    # 玩家的斗战点不足
    if user.base_att.douzhan < PVP_NEED_DOUZHAN:
        log.error('douzhan of user {0} have been zero!!!'.format( cid ))
        defer.returnValue( CHAR_DOUZHAN_NOT_ENOUGH )
    # 只能连续抢机器人
    if plunder_cid > 0:
        log.error('Can not plunder streak user. plunder_cid: {0}.'.format( plunder_cid ))
        defer.returnValue( REQUEST_LIMIT_ERROR )

    #抢夺，自动去除自己的免战
    yield redis.hdel( HASH_AVOID_WAR_TIME, cid ) 

    battle_count   = 0 # 抢夺的次数
    plunder_result = 0 # 未抢到
    new_shard      = []
    # 翻牌得到的幸运道具
    lottery_items = []
    for _i in range(0, 10):
        # 扣斗战点
        user.base_att.douzhan -= PVP_NEED_DOUZHAN
        # 抢夺次数加1
        battle_count += 1
        # 幸运道具奖励
        new_item = yield random_lottery_items( cid, user.level, user.base_att.vip_level, rand_count=1 )
        if len(new_item) > 0:
            lottery_items.append( new_item[0] )
        else:
            log.error('No lottery items. cid: {0}, level: {1}, vip_level: {2}.'.format( cid, level, vip_level ))
        # 随机碎片
        err, add_items = yield AvoidWarMgr.rand_shard( user, shard_id, plunder_cid )
        if not err and (len(add_items) > 0): #抢到
            plunder_result = 1
            syslogger(LOG_AVOID_WAR, cid, user.level, user.vip_level, user.alliance_id, 1, 1, add_items[0][0], add_items[0][2])
            new_shard = [add_items[0][0], add_items[0][2]]
            break
        # 玩家的斗战点不足
        if user.base_att.douzhan < PVP_NEED_DOUZHAN:
            log.error('douzhan of user {0} have been zero!!!'.format( cid ))
            break
    # 幸运道具进背包
    items_return = []
    for _type, _id, _num, _ in lottery_items:
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown decomposition item type. item type: {0}.'.format( _type ))
            continue
        res_err, res_value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_LOTTERY_AWARD, CapacityFlag=False)
        if not res_err:
            for _v in res_value:
                items_return = total_new_items(_v, items_return)
    # 每日任务计数
    yield user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_5, battle_count )
    # 开服七天
    yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_8, battle_count)
    yield user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_8, battle_count)

    defer.returnValue( (plunder_result, user.base_att.douzhan, new_shard, items_return, lottery_items) )


@route()
@defer.inlineCallbacks
def treasureshard_combine(p, req):
    '''
    @summary: 宝物碎片合成
    '''
    res_err = UNKNOWN_ERROR

    cid, [user_treasureshard_ids] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.bag_treasureshard_mgr.combine( user_treasureshard_ids )

    defer.returnValue( res_err )

