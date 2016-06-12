#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

import random
from marshal  import loads, dumps
from time     import time
from datetime import datetime
from errorno  import *
from constant import *
from redis    import redis
from log      import log
from utils    import timestamp_is_today, timestamp_is_week, check_joust_status, get_reward_timestamp, get_joust_reward_timestamp
from system   import get_vip_conf, get_arena_robot_rank, get_joust_exchange_conf, get_joust_buy_count_conf


from twisted.internet     import defer, reactor
from handler.character    import gs_offline_login, gs_offline_logout
from models.activity      import random_lottery_items
from models.item          import ITEM_MODELs
from models.award_center  import g_AwardCenterMgr
from protocol_manager     import ms_send


@defer.inlineCallbacks
def load_joust_user_data(cid, flag=False):
    ''' 
    @summary: 加载玩家的基本信息。
    @param: flag-是否加载阵容中的伙伴ID的标志位。
    '''
    _user_data, _fellow_ids = [], []
    _offline_user = yield gs_offline_login( cid )
    if _offline_user:
        if flag:
            _fellow_ids = yield _offline_user.fellow_mgr.get_camp_fellow_id()
        _alliance_info = (_offline_user.alliance_id, _offline_user.alliance_name)
        _user_data = [cid, _offline_user.lead_id, _offline_user.level, _offline_user.nick_name, _offline_user.might, _fellow_ids, _alliance_info]
        reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, cid)

    defer.returnValue( _user_data )

def load_robot_data(cid):
    '''
    @summary: 加载机器人的基本信息。机器人的CID范围是(1, 500), 已和玩家CID区分。
    '''
    robot_conf = get_arena_robot_rank( cid )
    if not robot_conf:
        robot_conf = get_arena_robot_rank( 1 )

    _robot_data = []
    if robot_conf:
        _fellow_ids = map(int, robot_conf['RobotList'].split(','))
        _robot_data = [cid, 0, robot_conf['RobotLevel'], robot_conf['RobotName'], 0, _fellow_ids, [0, ''], JOUST_BASIC_SCORE]
    else:
        log.error('No robot data in joust. cid: {0}.'.format( cid ))

    return _robot_data


class JoustMgr(object):
    '''
    @summary: 大乱斗
    '''
    def __init__(self):
        self.winner = []

    @defer.inlineCallbacks
    def joust_info(self, user):
        ''' 获取大乱斗的基本信息 '''
        _redis_key = SET_JOUST_CID_SCORE
        _is_open   = self.check_time_status()
        if _is_open == JOUST_HAD_END_ERROR:
            _redis_key = SET_JOUST_LAST_CID_SCORE
        _score = yield self.get_char_score(user.cid, _redis_key)
        _rank  = yield self.get_char_rank(user.cid, _redis_key)

        _joust_data, _status = yield self.get_joust_data(user.cid, _score, _rank)
        _left_count = JOUST_FREE_COUNT + _joust_data[2] - _joust_data[1]

        #_left_buy_count = 0
        #_vip_conf = get_vip_conf( user.vip_level )
        #if _vip_conf:
        #    _left_buy_count = _vip_conf['JoustCount'] - _joust_data[2]
        #    if _left_buy_count < 0:
        #        _left_buy_count = 0
 
        _details = yield self.get_joust_details(_joust_data[3])

        _next_timestamp = 0
        if not _status:
            _next_timestamp = get_reward_timestamp(JOUST_HOUR_END)
        elif 1 == _status:
            _next_timestamp = get_reward_timestamp(JOUST_HOUR_START)
        elif 2 == _status:
            _next_timestamp = get_joust_reward_timestamp(1, JOUST_HOUR_START)

        defer.returnValue( (_rank, _score, _left_count, JOUST_FREE_COUNT, _joust_data[4], _details, _status, _next_timestamp) )

    @defer.inlineCallbacks
    def refresh_players(self, user):
        ''' 刷新对手 '''
        _is_open   = self.check_time_status()
        if _is_open:
            defer.returnValue( _is_open )

        _score = yield self.get_char_score(user.cid)
        _rank  = yield self.get_char_rank(user.cid)

        _joust_data, _ = yield self.get_joust_data(user.cid, _score, _rank, True)
        _details = yield self.get_joust_details( _joust_data[3] )

        defer.returnValue( _details )

    @defer.inlineCallbacks
    def get_joust_data(self, cid, score, rank, flag=False):
        ''' 获取玩家的历史记录 
        @param: flag-强制刷新对手的标志位
        '''
        _changed = False # 数据变更的标志位
 
        _joust_data = yield redis.hget(HASH_JOUST_INFO, cid)
        if _joust_data:
            _joust_data = loads(_joust_data)
        else:
            _changed = True
            _joust_data = [int(time()), 0, 0, [], 0]

        _day_status, _time_status = check_joust_status( _joust_data[0] )
        # _time_status: 0-活动中 1-非活动时间 2-活动已结束
        if 2 == _time_status:
            if not self.winner:
                self.winner = yield redis.zrange( SET_JOUST_LAST_CID_SCORE, 0, 2 )
                _len = len(self.winner)
                for _i in range(_len, 3):
                    self.winner.append( _i + 1 )
            _joust_data[3] = self.winner

            defer.returnValue( (_joust_data, _time_status) )
        elif 0 == _time_status:
            # _day_status: 0-同一天 1-隔天 2-隔周
            if 1 == _day_status:
                _changed = True
                _joust_data = [int(time()), 0, _joust_data[2], _joust_data[3], 0]
            elif 2 == _day_status:
                _changed = True
                _joust_data = [int(time()), 0, 0, [], 0]

        if flag or (not _joust_data[3]):
            _changed = True
            _joust_data[3] = yield self.refresh_cids(cid, score, rank)

        if _changed:
            yield redis.hset(HASH_JOUST_INFO, cid, dumps(_joust_data))

        defer.returnValue( (_joust_data, _time_status) )

    @defer.inlineCallbacks
    def request_joust_battle(self, battle_type, user, position, status):
        ''' 
        @param: battle_type-挑战类型。1:普通挑战; 2:复仇
        @param: battle_type=1时position-挑战前对手的位置。1-上, 2-左, 3-右。battle_type=2时position=enemy_cid.
        @param: 战斗结果 status 0:lose, 1:win
        '''
        res_err  = []
        _is_open = self.check_time_status()
        # 判断是否处于活动时间
        if _is_open:
            defer.returnValue( _is_open )

        # 挑战次数是否充足
        _last_score = yield self.get_char_score(user.cid)
        _last_rank  = yield self.get_char_rank(user.cid)
        _joust_data, _ = yield self.get_joust_data(user.cid, _last_score, _last_rank)
        _left_count = JOUST_FREE_COUNT + _joust_data[2] - _joust_data[1]
        if _left_count < 1:
            defer.returnValue( JOUST_BATTLE_COUNT_NOT_ENOUGH )
        if _joust_data[2] > 0:
            _joust_data[2] -= 1
        else:
            _joust_data[1] += 1
        # 扣斗战点 2点
        if user.douzhan < PVP_NEED_DOUZHAN:
            defer.returnValue( CHAR_DOUZHAN_NOT_ENOUGH )
        user.base_att.douzhan -= PVP_NEED_DOUZHAN
        # 对手
        if battle_type == JOUST_BATTLE_NORMAL:
            _other_cid = _joust_data[3][position-1]
        else:
            _other_cid = position
        # 挑战失败, 给玩家 发送邮件
        if not status:
            ms_send('write_mail', (_other_cid, MAIL_PAGE_BATTLE, MAIL_BATTLE_4, [user.lead_id, user.nick_name]))
            yield redis.hset(HASH_JOUST_INFO, user.cid, dumps(_joust_data))
            if battle_type == JOUST_BATTLE_NORMAL:
                res_err = (_last_rank, _last_score, user.douzhan, _left_count-1, [], [], user.honor)
            else:
                res_err = (_last_score, user.douzhan, _left_count-1, [], user.honor)
            defer.returnValue( res_err )

        # win-荣誉/翻牌道具/刷新对手/邮件/积分/仇敌
        user.base_att.honor += JOUST_HONOR

        _score, _score_reduce = yield self.get_battle_score(user.cid, _other_cid)
        # 给玩家 发送邮件
        ms_send('write_mail', (_other_cid, MAIL_PAGE_BATTLE, MAIL_BATTLE_5, [user.lead_id, user.nick_name, _score_reduce]))
        # 翻牌道具
        _lottery_items = yield random_lottery_items( user.cid, user.level, user.vip_level )

        if battle_type == JOUST_BATTLE_NORMAL:
            # 新增仇敌 非机器人
            if _other_cid > JOUST_ROBOT_CID:
                yield self.update_enemy_cids(user.cid, _other_cid)
            # 刷新对手
            _rank = yield self.get_char_rank(user.cid)
            _joust_data[3] = yield self.refresh_cids(user.cid, _score, _rank)
            _details = yield self.get_joust_details(_joust_data[3])

            res_err = (_rank, _score, user.douzhan, _left_count-1, _lottery_items, _details, user.honor)
        else:
            # 挑战仇敌成功时，该仇敌移出列表
            if _other_cid > JOUST_ROBOT_CID:
                yield self.update_enemy_cids(_other_cid, user.cid, True)
                yield self.update_enemy_cids(user.cid, _other_cid)
            res_err = (_score, user.douzhan, _left_count-1, _lottery_items, user.honor)
        yield redis.hset(HASH_JOUST_INFO, user.cid, dumps(_joust_data))

        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def enemy_info(self, user):
        ''' 获取仇敌列表 '''
        _enemy_data = yield self.get_enemy_cids( user.cid )

        _details = yield self.get_joust_details( _enemy_data[1], flag=True )
        defer.returnValue( _details )

    @defer.inlineCallbacks
    def ranklist(self):
        ''' 
        @summary: 排行榜的前十名
        '''
        _ranklist  = []
        _redis_key = SET_JOUST_CID_SCORE
        _status = self.check_time_status()
        if _status == JOUST_HAD_END_ERROR:
            _redis_key = SET_JOUST_LAST_CID_SCORE
        _cid_scores = yield redis.zrange( _redis_key, 0, 9, withscores=True )
        for _idx, _data in enumerate(_cid_scores):
            _detail = yield load_joust_user_data( _data[0], flag=True )
            if not _detail:
                log.error('Unknown user. cid: {0}.'.format( _data[0] ))
                continue
            _detail.extend( [-int(_data[1]), _idx+1] )
            _ranklist.append( _detail )
 
        defer.returnValue( _ranklist )

    @defer.inlineCallbacks
    def buy_battle_count(self, user, buy_count):
        '''
        @param: buy_count-购买的次数
        '''
        _is_open   = self.check_time_status()
        if _is_open:
            defer.returnValue( _is_open )

        _joust_data = yield redis.hget(HASH_JOUST_INFO, user.cid)
        if _joust_data:
            _joust_data = loads(_joust_data)
            if not timestamp_is_today(_joust_data[0]):
                _joust_data[2] = 0
        else:
            _joust_data = [int(time()), 0, 0, [], 0]
        # 剩余免费挑战次数大于0, 不能购买, 策划要求
        if JOUST_FREE_COUNT > _joust_data[1]:
            defer.returnValue( JOUST_FREE_COUNT_ERROR )

        _vip_conf = get_vip_conf( user.vip_level )
        if not _vip_conf:
            log.error('No vip conf. cid: {0}, vip_level: {1}.'.format( user.cid, user.vip_level ))
            defer.returnValue( JOUST_BUY_COUNT_LIMIT_ERROR )
        # 剩余可购买次数
        _left_buy_count = _vip_conf['JoustCount'] - _joust_data[4]
        if _left_buy_count < buy_count:
            log.error('Buy count limit. cid: {0}, can buy: {1}, had buy: {2}.'.format( user.cid, _vip_conf['JoustCount'], _left_buy_count ))
            defer.returnValue( JOUST_BUY_COUNT_LIMIT_ERROR )
        #_left_buy_count -= buy_count
        # 所需钻石 
        _need_credits = get_joust_buy_count_conf(_joust_data[4]+1, _joust_data[4]+buy_count+1)
        if user.credits < _need_credits:
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )

        # 扣钻石
        user.consume_credits( _need_credits, WAY_JOUST_BATTLE_COUNT)
        # 增加次数
        _joust_data[2] += buy_count
        _joust_data[4] += buy_count
        yield redis.hset(HASH_JOUST_INFO, user.cid, dumps( _joust_data ))

        _left_count = JOUST_FREE_COUNT + _joust_data[2] - _joust_data[1]
        defer.returnValue( (_left_count, _joust_data[4], user.credits) )

    @defer.inlineCallbacks
    def get_exchange_status(self, user):
        ''' 获取已兑换道具的状态 
        @param: _data-[[last_timestamp, exchange_id, total_had_count, week_had_count, daily_had_count], ...]
        '''
        _data = yield redis.hget(HASH_JOUST_HONOR_EXCHANGE, user.cid)
        if _data:
            _data = loads(_data)
        else:
            _data = {}

        _exchanged = []
        for _d in _data.itervalues():
            _status = timestamp_is_week(_d[0])
            if 2 == _status: # 已隔周
                _exchanged.append( [_d[1], _d[2], 0, 0] )
            elif 1 == _status: # 已隔天
                _exchanged.append( [_d[1], _d[2], _d[3], 0] )
            else:
                _exchanged.append( _d[1:] )

        defer.returnValue( _exchanged )

    @defer.inlineCallbacks
    def exchange_items(self, user, exchange_id, exchange_count):
        ''' 荣誉兑换道具 '''
        conf = get_joust_exchange_conf( exchange_id )
        if not conf:
            log.error('Can not find conf. cid: {0}, exchange_id: {1}.'.format( user.cid, exchange_id ))
            defer.returnValue( NOT_FOUND_CONF )
        # 检查主角等级限制
        if user.base_att.level < conf['NeedLevel']:
            log.error('User level limit. cid: {0}, NeedLevel: {1}, cur level: {2}.'.format( user.cid, conf['NeedLevel'], user.base_att.level ))
            defer.returnValue( CHAR_LEVEL_LIMIT )

        cur_time = int(time())
        # read redis data
        _exchanged = yield redis.hget(HASH_JOUST_HONOR_EXCHANGE, user.cid)
        if _exchanged:
            _exchanged = loads(_exchanged)
        else:
            _exchanged = {}

        _old_excharge  = _exchanged.setdefault( exchange_id, [cur_time, exchange_id, 0, 0, 0] )
        _status = timestamp_is_week(_old_excharge[0])
        if 2 == _status: # 已隔周
            _old_excharge[3], _old_excharge[4] = 0, 0
        elif 1 == _status: # 已隔天
            _old_excharge[4] = 0
        # 检查可兑换次数限制
        if conf['MaxExchangeCount'] > 0:
            if (_old_excharge[2] + exchange_count) > conf['MaxExchangeCount']:
                defer.returnValue( JOUST_EXCHANGE_COUNT_ERROR )
        if conf['WeekExchangeCount'] > 0:
            if (_old_excharge[3] + exchange_count) > conf['WeekExchangeCount']:
                defer.returnValue( JOUST_EXCHANGE_COUNT_ERROR )
        if conf['DailyExchangeCount'] > 0:
            if (_old_excharge[4] + exchange_count) > conf['DailyExchangeCount']:
                defer.returnValue( JOUST_EXCHANGE_COUNT_ERROR )
        # 检查荣誉值
        _need_honor = exchange_count * conf['NeedHonor']
        if _need_honor > user.honor:
            defer.returnValue( CHAR_HONOR_NOT_ENOUGH )
        # 扣荣誉值
        user.base_att.honor -= _need_honor
        # 向背包中新增道具
        model = ITEM_MODELs.get( conf['ItemType'], None )
        if not model:
            log.error('Can not find model. item type: {0}.'.format( conf['ItemType'] ))
            defer.returnValue( ITEM_TYPE_ERROR )
        res_err, add_items = yield model( user, ItemID=conf['ItemID'], ItemNum=exchange_count*conf['ItemNum'], AddType=WAY_JOUST_EXCHANGE, CapacityFlag=False )
        if res_err:
            defer.returnValue( res_err )

        # 更新已兑换记录
        if conf['MaxExchangeCount'] > 0:
            _old_excharge[2] += exchange_count
        if conf['WeekExchangeCount'] > 0:
            _old_excharge[3] += exchange_count
        if conf['DailyExchangeCount'] > 0:
            _old_excharge[4] += exchange_count
        _exchanged[exchange_id] = _old_excharge
        yield redis.hset(HASH_JOUST_HONOR_EXCHANGE, user.cid, dumps(_exchanged))

        defer.returnValue( (user.honor, exchange_id, _old_excharge[2], _old_excharge[3], _old_excharge[4], add_items) )

    @defer.inlineCallbacks
    def get_char_rank(self, cid, redis_key=SET_JOUST_CID_SCORE):
        ''' 
        @return : rank=0时表示玩家没有排名. 
        '''
        _rank = yield redis.zrank(redis_key, cid)
        _rank = 0 if _rank is None else int(_rank)+1

        defer.returnValue( _rank )
 
    @defer.inlineCallbacks
    def get_char_score(self, cid, redis_key=SET_JOUST_CID_SCORE):
        ''' 获取玩家的积分 '''
        _score = yield redis.zscore(redis_key, cid)
        if _score is None:
            _score = JOUST_BASIC_SCORE
            yield redis.zadd(redis_key, cid, -JOUST_BASIC_SCORE)
        else:
            _score = -int(_score)

        defer.returnValue( _score )

    @defer.inlineCallbacks
    def refresh_cids(self, cid, score, rank):
        ''' 刷新CID '''
        _rank_start = rank
        _char_num   = 2 # 玩家的数量
        if score >= JOUST_BASIC_SCORE:
            _rank_start = rank - RANK_RANGE
            _rank_start = _rank_start if _rank_start > 0 else 0
            _char_num   = 3

        _cid_pools  = [] # 用于随机对手的cid池
        #log.info('For Test. random cid. _rank_start: {0}, _rank_end: {1}, req: {2}.'.format( _rank_start, rank + RANK_RANGE, (cid, score, rank) ))
        _cid_scores = yield redis.zrange(SET_JOUST_CID_SCORE, _rank_start, rank + RANK_RANGE, withscores=True)
        for _cid, _score in _cid_scores:
            if -int(_score) < JOUST_BASIC_SCORE:
                continue
            if _cid == cid:
                continue
            _cid_pools.append( _cid )

        if len(_cid_pools) > _char_num:
            _refresh_data = random.sample(_cid_pools, _char_num)
        else:
            _refresh_data = _cid_pools
        #log.info('For Test. refresh cids: {0}, _cid_pools len: {1}.'.format( _refresh_data, len(_cid_pools) ))
        _robot_num = 3 - len(_refresh_data)
        for _i in range(0, _robot_num):
            _refresh_data.append( random.randint(1, 500) )

        defer.returnValue( _refresh_data )

    def check_time_status(self):
        ''' 检查活动时间 '''
        _dt_now  = datetime.now()
        _weekday = _dt_now.isoweekday()
        if _weekday == SUNDAY or (_weekday == SATURDAY and _dt_now.hour >= JOUST_HOUR_END):
            return JOUST_HAD_END_ERROR
        elif _dt_now.hour < JOUST_HOUR_START or _dt_now.hour >= JOUST_HOUR_END:
            return JOUST_PERIOD_OF_TIME_ERROR

        return NO_ERROR

    @defer.inlineCallbacks
    def get_joust_details(self, cids, flag=False):
        ''' 获取玩家的对手详情 
        @param: flag-是否加载阵容中的伙伴ID的标志位。
        '''
        _all_details = []
        for _cid in cids:
            _detail = None
            if _cid > JOUST_ROBOT_CID:
                _detail = yield load_joust_user_data( _cid, flag )
                if _detail:
                    _score  = yield self.get_char_score( _cid )
                    _detail.append( _score )
            if not _detail:
                _detail = load_robot_data( _cid )
            _all_details.append( _detail )
 
        defer.returnValue( _all_details )

    @defer.inlineCallbacks
    def get_battle_score(self, cid, other_cid, redis_key=SET_JOUST_CID_SCORE):
        ''' 挑战胜利后计算积分 '''
        _score = yield self.get_char_score(cid)
        # 机器人
        _score_reduce = 0
        if other_cid < JOUST_ROBOT_CID:
            _other_score = JOUST_BASIC_SCORE
            if _score > _other_score:
                _score += SCORE_BASIC_2
            elif _score < _other_score:
                _score += SCORE_BASIC_4
            else:
                _score += SCORE_BASIC_3
 
            yield redis.zadd(redis_key, cid, -_score)
            defer.returnValue( (_score, _score_reduce) )
 
        # 玩家
        _other_score = yield self.get_char_score( other_cid )
        if _score > _other_score:
            _score_add = (_other_score * SCORE_RATE_2 + SCORE_PERCENT - 1) / SCORE_PERCENT
            _score_reduce = _score / SCORE_PERCENT
        elif _score < _other_score:
            _score_add = (_other_score * SCORE_RATE_4 + SCORE_PERCENT - 1) / SCORE_PERCENT + SCORE_BASIC_4
            _score_reduce = _score * SCORE_RATE_4 / SCORE_PERCENT
        else:
            _score_add = (_other_score * SCORE_RATE_3 + SCORE_PERCENT - 1) / SCORE_PERCENT + SCORE_BASIC_3
            _score_reduce = _score * SCORE_RATE_2 / SCORE_PERCENT

        #log.info('For Test. cid<{0}> score: {1} add<{2}>, other_cid<{3}> score: {4} reduce<{5}>.'.format( cid, _score, _score_add, other_cid, _other_score, _score_reduce ))
        _score += _score_add
        yield redis.zadd(redis_key, cid, -_score)
        _other_score = (_other_score - _score_reduce) if _other_score > _score_reduce else 0
        yield redis.zadd(redis_key, other_cid, -_other_score)

        defer.returnValue( (_score, _score_reduce) )

    @defer.inlineCallbacks
    def get_enemy_cids(self, cid):
        ''' '''
        _enemy_data = yield redis.hget(HASH_JOUST_ENEMY_INFO, cid)
        if _enemy_data:
            _enemy_data = loads(_enemy_data)
            if not timestamp_is_today(_enemy_data[0]):
                _enemy_data = [int(time()), []]
        else:
            _enemy_data = [int(time()), []]

        defer.returnValue( _enemy_data )

    @defer.inlineCallbacks
    def update_enemy_cids(self, cid, enemy_cid, deleted=False):
        ''' 新增仇敌
        @param: cid-攻击方
        @param: enemy_cid-被攻击方
        @param: deleted-True:从仇敌列表中清除enemy_cid, False:添加仇敌enemy_cid到仇敌列表
        '''
        _enemy_data = yield self.get_enemy_cids( enemy_cid )

        if deleted:
            if cid in _enemy_data[1]:
                _enemy_data[1].remove( cid )
                yield redis.hset( HASH_JOUST_ENEMY_INFO, enemy_cid, dumps(_enemy_data) )
        else:
            if cid not in _enemy_data[1]:
                _enemy_data[1].append( cid )
                if len(_enemy_data[1]) > JOUST_ENEMY_LIMIT:
                    del _enemy_data[1][0]
                yield redis.hset( HASH_JOUST_ENEMY_INFO, enemy_cid, dumps(_enemy_data) )

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def week_reward(self):
        '''
        @summary: 每周六 23:00 - 下周一 08:00发奖励, 且更新积分
        '''
        try:
            # 重置大乱斗数据
            yield self.reset_joust_data()
            # 发奖励
            _total_cids = yield redis.zcard(SET_JOUST_LAST_CID_SCORE)
            if _total_cids > 1:
                yield self.reward_to_award_center(_total_cids-1, 100)
        except Exception as e:
            log.exception()

        WEEK_AWARD_INTERVAL = get_joust_reward_timestamp() - int(time())
        log.warn('Next joust reward again after {0} seconds.'.format( WEEK_AWARD_INTERVAL ))
        reactor.callLater( WEEK_AWARD_INTERVAL, g_JoustMgr.week_reward )

    @defer.inlineCallbacks
    def reset_joust_data(self):
        ''' 重置大乱斗的数据 '''
        yield redis.delete( SET_JOUST_LAST_CID_SCORE )

        #_cid_scores = yield redis.zrange( SET_JOUST_CID_SCORE, 0, 9, withscores=True )
        #for _cid, _score in _cid_scores:
        #    yield redis.zadd( SET_JOUST_LAST_CID_SCORE, _cid, _score )
        yield redis.rename( SET_JOUST_CID_SCORE, SET_JOUST_LAST_CID_SCORE )
        yield redis.delete( HASH_JOUST_ENEMY_INFO )

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def reward_to_award_center(self, total_count, interval):
        try:
            timestamp  = int(time())
            start_rank = total_count - interval + 1 if total_count > interval else 0
            all_cids = yield redis.zrange( SET_JOUST_LAST_CID_SCORE, start_rank, total_count )
            for _idx, _cid in enumerate(all_cids):
                _rank = (_idx + start_rank + 1)
                yield g_AwardCenterMgr.new_award( _cid, AWARD_TYPE_JOUSTRANK, [timestamp, _rank] )
                # Reset score
                yield redis.zadd( SET_JOUST_CID_SCORE, _cid, -JOUST_BASIC_SCORE )
        except Exception as e:
            log.exception()
 
        if total_count > interval:
            total_count -= interval
            reactor.callLater( 1, self.reward_to_award_center, total_count, interval )
        #else:
        #    all_cids = yield redis.zrange( SET_JOUST_CID_SCORE, 0, -1 )
        #    log.warn('Reset joust score. total cids: {0}.'.format( len(all_cids) ))
        #    for _cid in all_cids:
        #        yield redis.zadd( SET_JOUST_CID_SCORE, _cid, -JOUST_BASIC_SCORE )

try:
    g_JoustMgr
except NameError:
    g_JoustMgr = JoustMgr()
    WEEK_AWARD_INTERVAL = get_joust_reward_timestamp() - int(time())
    log.warn('Next joust reward again after {0} seconds.'.format( WEEK_AWARD_INTERVAL ))
    reactor.callLater( WEEK_AWARD_INTERVAL, g_JoustMgr.week_reward )





