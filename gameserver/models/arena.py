#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from log      import log
from marshal  import loads, dumps
from time     import time
from datetime import datetime
from errorno  import *
from constant import *
from redis    import redis
from utils    import split_items, get_reward_timestamp, get_reset_timestamp

from twisted.internet     import defer, reactor
from system               import get_arena_robot_rank, get_total_robot_rank, get_arena_rank_award, get_activity_lottery, get_arena_exchange
from models.activity      import random_lottery_items, load_offline_user_info
from protocol_manager     import gw_broadcast, ms_send, alli_send
from models.award_center  import g_AwardCenterMgr
from models.item          import ITEM_MODELs
from manager.gsuser   import g_UserMgr
#from handler.character    import gs_offline_login, gs_offline_logout




@defer.inlineCallbacks
def arena_robot_data():
    '''
    modify 2014-10-28
    @param: detail data format: {rank: [cid, level, name, rank, golds, prestige, [fellow_id, ...], lead_id], ...}
    '''
    for _rank in range(1, 5001):
        _detail = dumps( [0, 0, '', _rank, 0, 0, [], 0] )
        yield redis.hset( HASH_ARENA_RANK, _rank, _detail )

    defer.returnValue( NO_ERROR )


class ArenaMgr(object):
    '''
    @summary: 竞技场
    @param  : SET_ARENA_CID_RANK member: cid, score: rank
    @param  : HASH_ARENA_RANK field:rank, value:[cid, level, name, rank, gold, prestige, [fellow_id, ...], lead_id]
    '''

    def get_rank_award(self, rank):
        ''' 返回竞技场中排名对应的奖励配置 '''
        award_gold, award_prestige = 1000, 50

        rank_award_conf = get_arena_rank_award( rank )
        if rank_award_conf:
            items_list = split_items( rank_award_conf['ArenaRankList'] )
            for _type, _id, _num in items_list:
                if _type == ITEM_TYPE_MONEY and _id == ITEM_MONEY_GOLDS:
                    award_gold = _num
                if _type == ITEM_TYPE_MONEY and _id == ITEM_MONEY_PRESTIGE:
                    award_prestige = _num
        return award_gold, award_prestige

    @defer.inlineCallbacks
    def get_all_char_rank(self):
        ''' rank: 0-没有排名
        '''
        _all_ranks = {}
        _cid_ranks = yield redis.zrange( SET_ARENA_CID_RANK, 0, -1, withscores=True )
        for _cid, _rank in _cid_ranks:
            _cids = _all_ranks.get(_rank, [])
            if _cid not in _cids:
                _cids.append( _cid )
                _all_ranks[_rank] = _cids
 
        defer.returnValue( _all_ranks )

    @defer.inlineCallbacks
    def get_all_rank_detail(self, flag=True):
        _data = []
        _all_details = yield redis.hgetall( HASH_ARENA_RANK )
        if not _all_details:
            defer.returnValue( _data )

        for rank, _detail in _all_details.iteritems():
            _detail = loads(_detail)
            if _detail[0] <= 0:
                continue

            if len(_detail) == 7:
                _detail.append( 0 )
            # 获取排名对应的奖励 及 阵容详情
            if flag:
                _detail[4], _detail[5] = self.get_rank_award( rank )
                # 排名上是个玩家, 加载玩家阵容
                if _detail[0] > 0:
                    major_level, fellow_ids, lead_id = yield load_offline_user_info(_detail[0])
                    if fellow_ids:
                        _detail[1] = major_level if major_level else _detail[1]
                        _detail[6] = fellow_ids
                        _detail[7] = lead_id
                else:
                    robot_conf = get_arena_robot_rank( rank )
                    _fellow_ids = map(int, robot_conf['RobotList'].split(','))
                    _detail[1], _detail[2], _detail[6] = robot_conf['RobotLevel'], robot_conf['RobotName'], _fellow_ids
            _data.append( (rank, _detail) )
 
        defer.returnValue( _data )

    @defer.inlineCallbacks
    def get_char_rank(self, cid):
        ''' rank: 0-没有排名
        '''
        _rank = yield redis.zscore( SET_ARENA_CID_RANK, cid )
        _rank = int(_rank) if _rank else 0

        defer.returnValue( _rank )

    @defer.inlineCallbacks
    def get_rank_detail(self, rank, flag=True):
        ''' 
        @summary: flag-是否需要加载玩家阵容中的fellow_ids及奖励, 默认加载
                并通过rank 获取 gold/prestige, 以及robot的name/level/fellow_ids
        '''
        if rank < 1 or rank > 5000:
            log.error('Error rank. rank: {0}, flag: {1}.'.format( rank, flag ))
            defer.returnValue( None )
        # 初始化机器人数据
        _exists = yield redis.exists( HASH_ARENA_RANK )
        if not _exists:
            yield arena_robot_data()
        # 获取排名对应的玩家或机器人
        _detail = yield redis.hget( HASH_ARENA_RANK, rank )
        if _detail:
            _detail = loads(_detail)
            if len(_detail) == 7:
                _detail.append( 0 )
            # 获取排名对应的奖励 及 阵容详情
            if flag:
                _detail[4], _detail[5] = self.get_rank_award( rank )
                # 排名上是个玩家, 加载玩家阵容
                if _detail[0] > 0:
                    major_level, fellow_ids, lead_id = yield load_offline_user_info(_detail[0])
                    if fellow_ids:
                        _detail[1] = major_level if major_level else _detail[1]
                        _detail[6] = fellow_ids
                        _detail[7] = lead_id
                else:
                    robot_conf = get_arena_robot_rank( rank )
                    _fellow_ids = map(int, robot_conf['RobotList'].split(','))
                    _detail[1], _detail[2], _detail[6] = robot_conf['RobotLevel'], robot_conf['RobotName'], _fellow_ids
            else:
                if _detail[0] == 0:
                    robot_conf = get_arena_robot_rank( rank )
                    _detail[1], _detail[2] = robot_conf['RobotLevel'], robot_conf['RobotName']
        else:
            log.error('No rank data. rank: {0}, flag: {1}.'.format( rank, flag ))
            _detail = [0, 0, '', rank, 0, 0, [], 0]
            yield redis.hset( HASH_ARENA_RANK, rank, dumps(_detail) )

            robot_conf = get_arena_robot_rank( rank )
            _fellow_ids = map(int, robot_conf['RobotList'].split(','))
            _detail[1], _detail[2], _detail[6] = robot_conf['RobotLevel'], robot_conf['RobotName'], _fellow_ids
 
        defer.returnValue( _detail )
 
    @defer.inlineCallbacks
    def arena_info(self, user):
        '''
        @summary: 获取竞技场信息
        '''
        total_rank = get_total_robot_rank()
        cur_rank   = yield self.get_char_rank( user.cid )
        arena_data = [cur_rank, get_reward_timestamp(hours=ARENA_RANK_REWARD_HOUR), []]
        enemy_rank = []
        if cur_rank == 0:
            # 全是机器人
            enemy_rank = sorted(random.sample(range(total_rank-300, total_rank), 7))
            for _rank in enemy_rank:
                _detail = yield self.get_rank_detail( _rank ) 
                if _detail:
                    arena_data[2].append( _detail )

            # 玩家第一次进入竞技场的时候，统一没有排名 没有排名奖励
            fellow_ids = yield user.fellow_mgr.get_camp_fellow_id()
            arena_data[2].append( [user.cid, user.level, user.nick_name, 0, 0, 0, fellow_ids, user.lead_id] )
            defer.returnValue( arena_data )
        elif cur_rank >= 3000:
            after_have = total_rank - cur_rank
            if after_have <= 300:
                enemy_rank = sorted(random.sample(range(cur_rank-300, cur_rank-1), 7))
                enemy_rank.append( cur_rank )
            else:
                enemy_rank = self.random_enemy_rank( cur_rank, 300 )
        elif cur_rank >= 1000:
            enemy_rank = self.random_enemy_rank( cur_rank, 200 )
        elif cur_rank >= 500:
            enemy_rank = self.random_enemy_rank( cur_rank, 100 )
        elif cur_rank >= 300:
            enemy_rank = self.random_enemy_rank( cur_rank, 50 )
        elif cur_rank >= 200:
            enemy_rank = self.random_enemy_rank( cur_rank, 30 )
        elif cur_rank >= 100:
            enemy_rank = self.random_enemy_rank( cur_rank, 10 )
        elif cur_rank > 5:
            enemy_rank = self.random_enemy_rank( cur_rank, 5 )
        else:
            enemy_rank = range(1, 9)#self.random_enemy_rank( cur_rank, cur_rank, cur_rank, 7-cur_rank )

        for _rank in enemy_rank:
            # 一定保证返回当前玩家的信息, 防止排行榜异常
            if _rank == cur_rank:
                _gold , _prestige = self.get_rank_award( _rank )
                fellow_ids = yield user.fellow_mgr.get_camp_fellow_id()
                arena_data[2].append( [user.cid, user.level, user.nick_name, _rank, _gold, _prestige, fellow_ids, user.lead_id] )
            else:
                _detail = yield self.get_rank_detail( _rank )
                if _detail:
                    arena_data[2].append( _detail )

        defer.returnValue( arena_data )

    def random_enemy_rank(self, cur_rank, interval, before_num=5, after_num=2):
        enemy_rank = sorted(random.sample(range(cur_rank-interval, cur_rank), before_num))
        enemy_rank.append( cur_rank )
        enemy_rank.extend( sorted(random.sample(range(cur_rank+1, cur_rank+interval), after_num)) )
        return enemy_rank

    @defer.inlineCallbacks
    def ranklist(self):
        ''' 
        @summary: 竞技场的排行榜的前十名
        '''
        _ranklist  = []
        _cid_ranks = yield redis.zrange( SET_ARENA_CID_RANK, 0, 9, withscores=True )
        for _cid, _rank in _cid_ranks:
            _detail = yield self.get_rank_detail( int(_rank) )
            if _detail and _detail[0] > 0:
                _ranklist.append( _detail )
 
        defer.returnValue( _ranklist )

    @defer.inlineCallbacks
    def lucky_ranklist(self):
        '''
        @summary: 幸运排名, 含本轮幸运排名和上轮幸运排名
        '''
        _lucky_data = [[], []]
        _data = yield redis.hget( HASH_ARENA_LUCKY_RANKLIST, LUCKY_RANKLIST )
        if _data:
            _lucky_data = loads( _data )
            for _l in _lucky_data[0]:
                if len(_l) == 3:
                    _l.append(0)

        # 还没有随机本轮的幸运排名
        if not _lucky_data[1]: 
            _lucky_rank = random.sample(range(1, 501), 10)
            for _rank in _lucky_rank[0:3]:
                _lucky_data[1].append( [_rank, 50] )
            for _rank in _lucky_rank[3:]:
                _lucky_data[1].append( [_rank, 25] )

            yield redis.hset( HASH_ARENA_LUCKY_RANKLIST, LUCKY_RANKLIST, dumps( _lucky_data ) )

        defer.returnValue( _lucky_data )

    @defer.inlineCallbacks
    def update_lucky_ranklist(self):
        '''
        @summary: 每晚22:00-22:15发放奖励时替换新旧幸运排名
        '''
        _lucky_data = yield self.lucky_ranklist()
        _old_data   = []
        _timestamp  = int(time())
        for _l in _lucky_data[1]:
            _detail = yield self.get_rank_detail( _l[0], flag=False )
            if _detail:
                _old_data.append( [_l[0], _detail[2], _l[1], _detail[7]] )
                if _detail[0] > 0:
                    # 给离线玩家钻石
                    yield g_AwardCenterMgr.new_award( _detail[0], AWARD_TYPE_ARENA_LUCKY, [_timestamp, [[ITEM_TYPE_MONEY, ITEM_MONEY_CREDITS, _l[1]]]], False )
                    #_user_lucky = yield gs_offline_login( _detail[0] )
                    #if _user_lucky:
                    #    _user_lucky.get_credits( _l[1], WAY_ARENA_LUCK_RANK )
                    #    reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, _detail[0])
                    #else:
                    #    log.warn('User login fail. lucky_cid: {0}.'.format( _detail[0] ))
        # 再次随机幸运排名
        _new_data   = []
        _lucky_rank = random.sample(range(1, 501), 10)
        for _rank in _lucky_rank[0:3]:
            _new_data.append( [_rank, 50] )
        for _rank in _lucky_rank[3:]:
            _new_data.append( [_rank, 25] )

        # write redis
        _lucky_data = [_old_data, _new_data]
        yield redis.hset( HASH_ARENA_LUCKY_RANKLIST, LUCKY_RANKLIST, dumps( _lucky_data ) )

    @defer.inlineCallbacks
    def lottery_items(self, user, client_my_rank, enemy_rank, battle_status):
        '''
        @summary: 挑战胜利后，替换双方的排名，并返回可供翻牌的道具列表。长度为3。
        '''
        items_list = []
        # 判断是否处于结算时间 22:00-22:15
        _dt_now    = datetime.now()
        if _dt_now.hour == ARENA_RANK_REWARD_HOUR and _dt_now.minute < 15:
            defer.returnValue( ARENA_IN_REWARD_TIME )

        # 扣斗战点 2点
        if user.base_att.douzhan < PVP_NEED_DOUZHAN:
            log.error('user douzhan is 0. cid: {0}.'.format( user.cid ))
            defer.returnValue( CHAR_DOUZHAN_NOT_ENOUGH )
        user.base_att.douzhan -= PVP_NEED_DOUZHAN

        # 获取我的排名
        my_rank = yield self.get_char_rank( user.cid )
        if my_rank != client_my_rank:
            log.error('Client arena rank info need update. cid: {0}, client_my_rank: {1}, my_rank: {2}.'.format( user.cid, client_my_rank, my_rank ))
        # 每日任务计数
        yield user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_6, 1 )

        if not battle_status:
            # 失败获得10声望值
            user.get_prestige( 10, WAY_ARENA_BATTLE )
            enemy_detail = yield self.get_rank_detail( enemy_rank, flag=False )
            if not enemy_detail:
                log.error('No enemy rank data. cid: {0}, enemy_rank: {1}.'.format( user.cid, enemy_rank ))
                defer.returnValue( (items_list, user.base_att.douzhan) )

            ms_send('write_mail', (enemy_detail[0], MAIL_PAGE_BATTLE, MAIL_BATTLE_1, [user.base_att.lead_id, user.base_att.nick_name]))
            defer.returnValue( (items_list, user.base_att.douzhan) )

        # 胜利获得20声望值
        user.get_prestige( 20, WAY_ARENA_BATTLE )
        items_list = yield random_lottery_items( user.cid, user.base_att.level, user.base_att.vip_level )
        # 名次越靠前, 数字越小; 没有排名时也直接替换
        enemy_detail = yield self.get_rank_detail( enemy_rank, flag=False )
        if not enemy_detail:
            log.error('No enemy rank data. cid: {0}, enemy_rank: {1}.'.format( user.cid, enemy_rank ))
            defer.returnValue( (items_list, user.base_att.douzhan) )
        if my_rank == 0 or enemy_rank < my_rank:
            # 对方是玩家时 互换玩家信息
            if enemy_detail[0] > 0:
                old_enemy_rank = yield self.get_char_rank( enemy_detail[0] )
                if my_rank == 0: # 在排名5000(机器人总数)之外
                    yield redis.zrem( SET_ARENA_CID_RANK, enemy_detail[0] )
                    alli_send('sync_char_data', (enemy_detail[0], SYNC_ARENA_RANK, 0))
                else:
                    if old_enemy_rank == enemy_rank:
                        ms_send('write_mail', (enemy_detail[0], MAIL_PAGE_BATTLE, MAIL_BATTLE_2, [user.base_att.lead_id, user.base_att.nick_name, my_rank]))
                        yield redis.zadd( SET_ARENA_CID_RANK, enemy_detail[0], my_rank )
                        alli_send('sync_char_data', (enemy_detail[0], SYNC_ARENA_RANK, my_rank))
                        old_rank_detail = dumps( [enemy_detail[0], enemy_detail[1], enemy_detail[2], my_rank, 0, 0, [], enemy_detail[7]] )
                        yield redis.hset( HASH_ARENA_RANK, my_rank, old_rank_detail )
            elif my_rank > 0: # 对手是机器人, 恢复当前排名机器人数据
                old_rank_detail = dumps( [0, 0, '', my_rank, 0, 0, [], 0] )
                yield redis.hset( HASH_ARENA_RANK, my_rank, old_rank_detail )

            # 更新自己的rank数据
            yield redis.zadd( SET_ARENA_CID_RANK, user.cid, enemy_rank )
            alli_send('sync_char_data', (user.cid, SYNC_ARENA_RANK, enemy_rank))
            # 保存当前的camp
            #yield user.sync_camp_to_redis(update=True)
            new_rank_detail = dumps( [user.cid, user.level, user.nick_name, enemy_rank, 0, 0, [], user.lead_id] )
            yield redis.hset( HASH_ARENA_RANK, enemy_rank, new_rank_detail )
            # 夺得竞技场前十名, 全服广播
            if enemy_rank < 11:
                message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_ARENA, [user.base_att.nick_name, enemy_rank]]]
                gw_broadcast('sync_broadcast', [message])
        elif enemy_rank > my_rank:
            ms_send('write_mail', (enemy_detail[0], MAIL_PAGE_BATTLE, MAIL_BATTLE_3, [user.base_att.lead_id, user.base_att.nick_name]))
        #开服狂欢
        enemy_rank = enemy_rank if enemy_rank < my_rank else my_rank
        yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_7, enemy_rank)
        yield user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_7, enemy_rank)
        defer.returnValue( (items_list, user.base_att.douzhan) )

    @defer.inlineCallbacks
    def daily_reward(self):
        '''
        @summary: 每日22:00-22:15发放奖励, 且更新幸运排名
        '''
        try:
            # 发奖励
            yield self.reward_to_award_center()
            # 更新幸运排名, 并发放钻石
            yield self.update_lucky_ranklist()
        except Exception as e:
            log.error('Exception e: {0}.'.format( e ))

        # for test
        DAILY_AWARD_INTERVAL = get_reward_timestamp(hours=ARENA_RANK_REWARD_HOUR) - int(time())
        log.debug('Next 22:00 after {0} seconds will reward again.'.format( DAILY_AWARD_INTERVAL ))
        reactor.callLater( DAILY_AWARD_INTERVAL, g_ArenaMgr.daily_reward )

    @defer.inlineCallbacks
    def reward_to_award_center(self, total_rank=4999, interval=99):
        try:
            timestamp = int(time())
            cid_ranks = yield redis.zrange( SET_ARENA_CID_RANK, total_rank-interval, total_rank, withscores=True )
            if cid_ranks:
                log.debug('redis start: {0}, stop: {1}, cid_ranks: {2}.'.format( total_rank-interval, total_rank, cid_ranks ))
            for _cid, _rank in cid_ranks:
                yield g_AwardCenterMgr.new_award( int(_cid), AWARD_TYPE_ARENARANK, [timestamp, int(_rank)], False )
                #rank_award_conf = get_arena_rank_award( int(_rank) )
                #if rank_award_conf:
                #    items_list = split_items( rank_award_conf['ArenaRankList'] )
                #    ms_send('write_mail', (_cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_1, [timestamp, int(_rank), items_list]))
        except Exception as e:
            log.error('Exception e: {0}.'.format( e ))

        if total_rank  > interval:
            total_rank -= (interval + 1)
            reactor.callLater( 2, self.reward_to_award_center, total_rank, interval )

    @defer.inlineCallbacks
    def exchange_status(self, cid):
        '''
        @summary: 竞技场中 声望兑换的记录
        @param  : data-[update_time, exchange_id, total_count, daily_count]
        '''
        data = yield redis.hget(HASH_ARENA_EXCHANGE, cid)
        if data:
            data = loads(data)
        else:
            data = {}

        status = []
        reset_timestamp = get_reset_timestamp()
        for _v in data.itervalues():
            # 上次兑换时间已非今日
            if _v[0] <= reset_timestamp:
                status.append( [_v[1], _v[2], 0] )
            else:
                status.append( [_v[1], _v[2], _v[3]] )
 
        defer.returnValue( status )

    @defer.inlineCallbacks
    def exchange(self, user, exchange_id, exchange_count):
        '''
        @summary: 竞技场中 用声望兑换道具
        '''
        conf = get_arena_exchange( exchange_id )
        if not conf:
            log.error('Can not find conf. exchange_id: {0}.'.format( exchange_id ))
            defer.returnValue( NOT_FOUND_CONF )
        # 检查主角等级限制
        if user.base_att.level < conf['NeedLevel']:
            log.error('User level limit. NeedLevel: {0}, cur level: {1}.'.format( conf['NeedLevel'], user.base_att.level ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        cur_time = int(time())
        # read redis data
        data = yield redis.hget(HASH_ARENA_EXCHANGE, user.cid)
        if data:
            data = loads(data)
        else:
            data = {}

        old_excharge    = data.setdefault( exchange_id, [cur_time, exchange_id, 0, 0] )
        reset_timestamp = get_reset_timestamp()
        if old_excharge[0] <= reset_timestamp:
            old_excharge[0] = cur_time
            old_excharge[3] = 0
        # 检查可兑换次数限制
        if conf['MaxExchangeCount'] > 0:
            if (old_excharge[2] + exchange_count) > conf['MaxExchangeCount']:
                log.error('max count: {0}, used count: {1}, exchange_count: {2}.'.format( conf['MaxExchangeCount'], old_excharge[2], exchange_count ))
                defer.returnValue( ARENA_EXCHANGE_MAX_NUM )
        if conf['DailyExchangeCount'] > 0:
            if (old_excharge[3] + exchange_count) > conf['DailyExchangeCount']:
                log.error('daily_max_count: {0}, used count: {1}, exchange_count: {2}.'.format( conf['DailyExchangeCount'], old_excharge[3], exchange_count ))
                defer.returnValue( ARENA_EXCHANGE_MAX_NUM )
        # 检查声望值
        need_prestige = exchange_count * conf['NeedPrestige']
        if need_prestige > user.base_att.prestige:
            log.error('prestige. need: {0}, cur: {1}.'.format( need_prestige, user.base_att.prestige ))
            defer.returnValue( CHAR_PRESTIGE_NOT_ENOUGH )
        # 扣声望值
        user.consume_prestige( need_prestige, WAY_ARENA_EXCHANGE )
        # 向背包中新增道具
        model = ITEM_MODELs.get( conf['ItemType'], None )
        if not model:
            log.error('Can not find model. item type: {0}.'.format( conf['ItemType'] ))
            defer.returnValue( ITEM_TYPE_ERROR )
        res_err, add_items = yield model( user, ItemID=conf['ItemID'], ItemNum=exchange_count*conf['ItemNum'], AddType=WAY_ARENA_EXCHANGE, CapacityFlag=False )
        if res_err:
            defer.returnValue( res_err )

        # 更新已兑换记录
        if conf['MaxExchangeCount'] > 0:
            old_excharge[2] += exchange_count
        if conf['DailyExchangeCount'] > 0:
            old_excharge[3] += exchange_count
        yield redis.hset(HASH_ARENA_EXCHANGE, user.cid, dumps(data))

        defer.returnValue( (user.base_att.prestige, old_excharge[2], old_excharge[3], add_items) )



try:
    g_ArenaMgr
except NameError:
    g_ArenaMgr = ArenaMgr()
    DAILY_AWARD_INTERVAL = get_reward_timestamp(hours=ARENA_RANK_REWARD_HOUR) - int(time())
    reactor.callLater( DAILY_AWARD_INTERVAL, g_ArenaMgr.daily_reward )

