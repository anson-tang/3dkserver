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


@route()
@defer.inlineCallbacks
def get_scene_group(p, req):
    '''return: Array(Array(town_id,passed,cur_star,sweep_flag), ...)
    @passed: 通关状态,0-未通关, 1-已通关
    @sweep_flag: 全扫荡状态, 0-不可扫荡, 1-可以全扫荡
    '''
    res_err = UNKNOWN_ERROR
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    all_scene = yield user.scene_mgr.all_scene_group()

    defer.returnValue( all_scene )

@route()
@defer.inlineCallbacks
def get_scene_group_new(p, req):
    ''' v0.3.3.2以后使用的协议
    @return: Array(had_sweep, Array(Array(town_id,passed,cur_star,sweep_flag), ...))
    @passed: 通关状态,0-未通关, 1-已通关
    @sweep_flag: 全扫荡状态, 0-不可扫荡, 1-可以全扫荡
    @had_sweep: 当天已全扫荡的次数
    '''
    res_err = UNKNOWN_ERROR
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
 
    all_scene  = yield user.scene_mgr.all_scene_group()
    daily_info = yield user.scene_mgr.get_scene_reset_daily()

    defer.returnValue( (all_scene, daily_info[1], daily_info[2], daily_info[3]) )


@route()
@defer.inlineCallbacks
def get_monster_group(p, req):
    res_err = UNKNOWN_ERROR
    cid, [ scene_id ] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    all_dungeon = yield user.scene_mgr.all_dungeon_group( scene_id )
    defer.returnValue( all_dungeon )

@route()
@defer.inlineCallbacks
def get_monster_group_new(p, req):
    res_err = UNKNOWN_ERROR
    cid, [ scene_id ] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    all_dungeon = yield user.scene_mgr.all_dungeon_group_new( scene_id )
    defer.returnValue( all_dungeon )

@route()
@defer.inlineCallbacks
def multi_monster_group(p, req):
    res_err = UNKNOWN_ERROR
    cid, scene_ids = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    all_dungeon = yield user.scene_mgr.multi_dungeon_group( scene_ids )
    defer.returnValue( all_dungeon )

@route()
@defer.inlineCallbacks
def start_battle(p, req):
    res_err = UNKNOWN_ERROR
    cid, ( battle_type, scene_id, dungeon_id, dungeon_star ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    if battle_type == FIGHT_TYPE_NORMAL: # 剧情副本战斗 
        res_err = yield user.scene_mgr.start_battle(scene_id, dungeon_id, dungeon_star)
    elif battle_type == FIGHT_TYPE_ELITE: # 精英副本战斗
        res_err = yield user.elitescene_mgr.start_battle(scene_id)
    elif battle_type in (FIGHT_TYPE_PANDA, FIGHT_TYPE_TREASURE, FIGHT_TYPE_TREE): # 活动副本战斗
        res_err = yield user.activescene_mgr.start_battle(scene_id)
    elif battle_type == FIGHT_TYPE_CLIMBING: # 天外天战斗
        res_err = NO_ERROR

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def request_battle_reward(p, req):
    res_err = UNKNOWN_ERROR

    cid, [ battle_type, status, scene_id, dungeon_id, dungeon_star ] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    if battle_type == FIGHT_TYPE_NORMAL: # 剧情副本战斗 
        res_err = yield user.scene_mgr.get_battle_reward(status, scene_id, dungeon_id, dungeon_star)
    elif battle_type == FIGHT_TYPE_ELITE: # 精英副本战斗
        res_err = yield user.elitescene_mgr.get_battle_reward(status, scene_id)
    elif battle_type in (FIGHT_TYPE_PANDA, FIGHT_TYPE_TREASURE, FIGHT_TYPE_TREE): # 活动副本战斗
        res_err = yield user.activescene_mgr.get_battle_reward(battle_type, status, scene_id)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def elitescene_data(p, req):
    res_err = UNKNOWN_ERROR
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.elitescene_mgr.elitescene_data()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def activescene_data(p, req):
    res_err = UNKNOWN_ERROR
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.activescene_mgr.activescene_data()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def buy_battle_count(p, req):
    res_err = UNKNOWN_ERROR
    cid, [battle_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    if battle_type == FIGHT_TYPE_ELITE:
        res_err = yield user.elitescene_mgr.buy_count()
    elif battle_type in (FIGHT_TYPE_PANDA, FIGHT_TYPE_TREASURE, FIGHT_TYPE_TREE): # 活动副本战斗
        res_err = yield user.activescene_mgr.buy_count(battle_type)

    defer.returnValue( res_err )

@route()
def battle_fellow_revive(p, req):
    res_err = UNKNOWN_ERROR
    cid, [battle_type] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return res_err

    if battle_type == FIGHT_TYPE_ELITE: # 精英副本战斗 
        res_err = user.elitescene_mgr.battle_revive()
    elif battle_type in (FIGHT_TYPE_TREASURE, FIGHT_TYPE_TREE): # 活动副本战斗
        res_err = user.activescene_mgr.battle_revive(battle_type)

    return res_err

@route()
@defer.inlineCallbacks
def battle_win_streak(p, req):
    '''
    @summary: 连续n次战斗
    '''
    res_err = UNKNOWN_ERROR

    cid, [scene_id, dungeon_id, dungeon_star, battle_count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    if battle_count <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res_err = yield user.scene_mgr.win_streak( scene_id, dungeon_id, dungeon_star, battle_count )
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def buy_battle_cd_time(p, req):
    '''
    清除连战冷却时间 60s = 1 credits
    '''
    res_err = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.scene_mgr.buy_cd_time()
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def battle_scene_sweep(p, req):
    ''' 剧情副本全扫荡, 掉落的道具通过领奖中心发放
    '''
    cid, [scene_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    #res_err = user.check_function_open(FUNCTION_SCENE_SWEEP)
    #if res_err:
    #    defer.returnValue( res_err )

    res_err = yield user.scene_mgr.scene_all_sweep(scene_id)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def battle_scene_sweep_new(p, req):
    ''' 剧情副本全扫荡, 掉落的道具通过领奖中心发放
    '''
    cid, [scene_id, sweep_way] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    #res_err = user.check_function_open(FUNCTION_SCENE_SWEEP)
    #if res_err:
    #    defer.returnValue( res_err )

    res_err = yield user.scene_mgr.scene_all_sweep(scene_id, sweep_way)
    defer.returnValue( res_err )

@route()
def scene_star_rewarded(p, req):
    res_err = UNKNOWN_ERROR

    cid, [scene_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return res_err

    res_err = user.scene_mgr.get_star_rewarded(scene_id)

    return res_err

@route()
@defer.inlineCallbacks
def get_scene_star_reward(p, req):
    ''' scene_star_count-副本获得的星星数量 '''
    res_err = UNKNOWN_ERROR
    cid, [scene_id, scene_star_count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    res_err = yield user.scene_mgr.scene_star_reward(scene_id, scene_star_count)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def update_chaos(p, req):
    res_err = UNKNOWN_ERROR

    cid, [next_level] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue(res_err)

    res_err = user.update_chaos( next_level )
    # 开服七天
    yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_11, res_err[0] )
    #成就
    yield user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_11, res_err[0])

    defer.returnValue(res_err)

@route()
@defer.inlineCallbacks
def get_scene_ranklist(p, req):
    ''' 获取剧情排行榜前10名 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.scene_mgr.ranklist()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_dungeon_reward(p, req):
    cid, [scene_id, dungeon_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.scene_mgr.dungeon_reward(scene_id, dungeon_id)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def reset_monster_count(p, req):
    cid, [scene_id, dungeon_id, reset_way] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.scene_mgr.reset_dungeon_count(scene_id, dungeon_id, reset_way)

    defer.returnValue( res_err )


@route()
@defer.inlineCallbacks
def auto_update_chaos(p, req):
    res_err = UNKNOWN_ERROR

    cid, [tar_level]= req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue(res_err)

    res_err = user.update_chaos_auto(tar_level)
    if isinstance(res_err, int):
        defer.returnValue(res_err)
    # 开服七天
    yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_11, res_err[0] )
    #成就
    yield user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_11, res_err[0])

    defer.returnValue(res_err)
