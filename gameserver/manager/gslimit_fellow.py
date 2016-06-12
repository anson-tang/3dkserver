#!/USR/BIN/ENV PYTHON
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from twisted.internet       import defer


from time     import time
from datetime import datetime
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     
from utils    import datetime2time, rand_num
from syslogger import syslogger

from system   import get_limit_fellow_conf, get_limit_fellow_level, get_fellow_by_fid, \
        get_limit_fellow_pool_levels, get_limit_fellow_pool_conf, get_limit_fellow_award_conf, \
        get_excite_activity_conf

from protocol_manager       import gw_broadcast
from models.award_center    import g_AwardCenterMgr
from twisted.internet       import defer, reactor


class GSLimitFellowMgr(object):
    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

    @defer.inlineCallbacks
    def status(self):
        ''' 限时神将的状态 
        param status: -1:无活动 0:无免费次数 1:有免费次数 
        '''
        _activity = get_limit_fellow_conf()
        if not _activity:
            defer.returnValue( (-1, None) )
        _need_time = 0

        _data = yield redis.hget(HASH_LIMIT_FELLOW_SHRINE, self.cid)
        if _data:
            _data = loads(_data)
            if _data[0] == _activity['ActivityID']:
                _need_time = self.left_free_timestamp( _data[3], LIMIT_FELLOW_FREE_TIME )
                if _need_time > 0:
                    defer.returnValue( (0, _data) )
                else:
                    defer.returnValue( (1, _data) )
        # 抽卡次数从1开始，卡池升级后抽卡次数为0
        _data = [_activity['ActivityID'], 0, 1, 0]
        yield redis.hset(HASH_LIMIT_FELLOW_SHRINE, self.cid, dumps( _data ))
        defer.returnValue( (1, _data) )

    @defer.inlineCallbacks
    def limit_fellow_info(self):
        ''' 限时神将基本信息 '''
        _status, _data = yield self.status()
        if _status < 0:
            defer.returnValue( LIMIT_FELLOW_NO_ERROR )

        _all_lvl_conf = get_limit_fellow_level()
        if not _all_lvl_conf:
            log.error('Can not find limit fellow shrine level update conf.')
            defer.returnValue( NOT_FOUND_CONF )
        _all_lvls  = _all_lvl_conf.keys()
        _max_level = max(_all_lvls)
        if _data[1] >= _max_level:
            _shrine_level = _max_level
        else:
            _shrine_level = _data[1] + 1
        _shrine_conf = _all_lvl_conf[_shrine_level]
        _need_count  = _shrine_conf['RandCount'] - _data[2] if _shrine_conf['RandCount'] > _data[2] else 0
        _need_time   = self.left_free_timestamp( _data[3], LIMIT_FELLOW_FREE_TIME )

        _rank, _score = yield self.get_name_info( self.user.nick_name )
        _ranklist = yield self.ranklist()

        defer.returnValue( (_data[0], _rank, _score, _need_time, _need_count, _ranklist, LIMIT_FELLOW_RAND_COST) )


    @defer.inlineCallbacks
    def ranklist(self):
        ''' 积分排行榜的前20名 '''
        _ranklist = []
        _name_scores = yield redis.zrevrange( SET_LIMIT_FELLOW_NAME_SCORE, 0, 19, withscores=True )
        _rank = 1
        for _nick_name, _score in _name_scores:
            _ranklist.append( [_rank, str(_nick_name), _score] )
            _rank += 1

        defer.returnValue( _ranklist )

    @defer.inlineCallbacks
    def get_name_info(self, nick_name):
        _score = yield redis.zscore( SET_LIMIT_FELLOW_NAME_SCORE, nick_name )
        _score = int(_score) if _score else 0
        # 第一名返回rank=0, 没有rank为None
        _rank  = yield redis.zrevrank( SET_LIMIT_FELLOW_NAME_SCORE, nick_name )
        _rank  = int(_rank) + 1 if _rank >= 0 else 0

        defer.returnValue( (_rank, _score) )

    def left_free_timestamp(self, last_free_time, rand_free_time):
        '''
        @summary: 免费抽奖的倒计时剩余时间
        @param  : last_free_time-上次免费抽奖的时间, 0代表还未免费抽过奖
        @param  : rand_free_time-免费抽奖时间的周期
        @param  : need_time-距离下一次免费抽奖还需要的时间
        '''
        need_time = 0
        if last_free_time:
            need_time = int(last_free_time + rand_free_time - time())
            if need_time < 0:
                need_time = 0
 
        return need_time

    @defer.inlineCallbacks
    def randcard(self, rand_type):
        ''' 免费抽卡、钻石抽卡 '''
        _status, _data = yield self.status()
        if _status < 0:
            defer.returnValue( LIMIT_FELLOW_NO_ERROR )
        _need_time = self.left_free_timestamp( _data[3], LIMIT_FELLOW_FREE_TIME )
        _last_time = _data[3]
        # 检查抽卡条件是否满足
        _score = yield redis.zscore( SET_LIMIT_FELLOW_NAME_SCORE, self.user.nick_name )
        _score = int(_score) if _score else 0
        _cost_flag = True # 扣钻石的标识位
        if rand_type == RANDCARD_TYPE_FREE:
            if _need_time > 0:
                defer.returnValue( LIMIT_FELLOW_FREE_ERROR )
            else:
                _last_time = int(time())
                _cost_flag = False
                _need_time = LIMIT_FELLOW_FREE_TIME
        else:
            # 某积分的整数倍时免费钻石抽卡
            if not _score or _score%RAND_COST_FREE_SCORE != 0:
                if self.user.credits < LIMIT_FELLOW_RAND_COST:
                    defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            else:
                _cost_flag = False
        # 卡池升级
        res_err, shrine_data = self.update_shrine(_data[1], _data[2])
        if res_err:
            defer.returnValue( res_err )
        #log.info('For Test. shrine_data: {0}, redis_data: {1}.'.format( shrine_data, _data ))
        # 获取抽卡池并抽卡
        card_conf = self.get_randcard_frompool(_data[1], shrine_data[3]-_data[2])
        if not card_conf:
            defer.returnValue( NOT_FOUND_CONF )

        # 更新免费时间或扣钻石
        yield redis.hset( HASH_LIMIT_FELLOW_SHRINE, self.cid, dumps([_data[0], shrine_data[0], shrine_data[1], _last_time]) )
        if _cost_flag:
            yield self.user.consume_credits( LIMIT_FELLOW_RAND_COST, WAY_LIMIT_FELLOW_RANDCARD )
        _score += RANDCARD_ONCE_SCORE
        yield redis.zadd( SET_LIMIT_FELLOW_NAME_SCORE, self.user.nick_name, _score )
        # 新增fellow
        try:
            # args: fellow_id, is_major, camp_id, on_troop
            new_fellow = []
            fellow_id  = card_conf['ItemId']
            res_err, attrib = yield self.user.fellow_mgr.create_table_data( fellow_id, 0, 0, 0 )
            if not res_err:
                new_fellow = [attrib.attrib_id, fellow_id]
                conf = get_fellow_by_fid( fellow_id )
                if conf and conf['Quality'] == QUALITY_PURPLE:
                    syslogger(LOG_FELLOW_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, \
                            attrib.attrib_id, fellow_id, conf['QualityLevel'], conf['Star'], RANDCARD_TYPE_CREDITS, '')
                    message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_LIMIT_FELLOW, [self.user.nick_name, fellow_id]]]
                    gw_broadcast('sync_broadcast', [message])
        except Exception as e:
            log.warn('Create fellow fail! e:', e)
            defer.returnValue(res_err)

        _rank  = yield redis.zrevrank( SET_LIMIT_FELLOW_NAME_SCORE, self.user.nick_name )
        _rank  = int(_rank) + 1 if _rank >= 0 else 0
        _ranklist = yield self.ranklist()
        defer.returnValue( [self.user.credits, _rank, _score, _need_time, shrine_data[2], _ranklist, new_fellow] )

    def get_randcard_frompool(self, shrine_level, rand_count):
        ''' 获取抽卡池 '''
        pool_level = 0
        if rand_count == 0:
            pool_level = shrine_level + 1

        final_level = 0
        all_shrine_levels = get_limit_fellow_pool_levels()
        for _level in all_shrine_levels:
            if _level <= pool_level and final_level < _level:
                final_level = _level

        total_rate = 0
        pool = get_limit_fellow_pool_conf(final_level)
        for _conf in pool.itervalues():
            total_rate += _conf['Rate']

        if total_rate <= 0:
            log.warn('No randcard. final_level: {0}, total_rate: {1}.'.format( final_level, total_rate ))
            return {}

        curr_int = 0
        randint  = rand_num(total_rate)
        for _conf in pool.itervalues():
            if randint < (curr_int + _conf['Rate']):
                #log.error('For Test. randint: {0}, curr_int: {1}, rate: {2}, total_rate: {3}.'.format( randint, curr_int, _conf['Rate'], total_rate ))
                return _conf
            else:
                curr_int += _conf['Rate']
        else:
            log.warn('Not rand a card. final_level: {0}, randint: {1}, total_rate: {2}.'.format( final_level, randint, total_rate ))
            return {}

    def update_shrine(self, level, count):
        ''' 神坛升级 '''
        count += 1
        all_lvl_conf = get_limit_fellow_level()
        if not all_lvl_conf:
            log.error('Can not find limit fellow shrine level update conf.')
            return NOT_FOUND_CONF, None
        all_lvls     = all_lvl_conf.keys()
        max_level    = max(all_lvls)
        next_level   = level + 1 if (level+1) < max_level else max_level

        shrine_conf  = all_lvl_conf[next_level]
        if count > shrine_conf['RandCount']:
            count = 0
            if level < max_level:
                level = next_level

        return NO_ERROR, (level, count, shrine_conf['RandCount']-count, shrine_conf['RandCount'])


@defer.inlineCallbacks
def grant_limit_fellow_award(all_ranks, activity_id, timestamp):
    '''
    @param: timestamp-借用时间戳作为callLater的有效性验证
    '''
    log.warn('limit fellow award. activity_id: {0}, timestamp: {1}, ACTIVITY_AWARD_TIME: {2}.'.format( activity_id, timestamp, ACTIVITY_AWARD_TIME ))
    # 判断是否是正确的callLater
    if ACTIVITY_AWARD_TIME != timestamp:
        defer.returnValue( None )

    _max_rank = max(all_ranks)
    if _max_rank > 0:
        _rank = 1
        _name_scores = yield redis.zrevrange( SET_LIMIT_FELLOW_NAME_SCORE, 0, _max_rank, withscores=True )
        for _nick_name, _score in _name_scores:
            if _score <= 0:
                continue
            _cid = yield redis.hget(DICT_NICKNAME_REGISTERED, str(_nick_name))
            if _cid:
                yield g_AwardCenterMgr.new_award( _cid, AWARD_TYPE_LIMIT_FELLOW_RANK, [int(time()), activity_id, _rank] )
            _rank += 1

    if 0 in all_ranks:
        _names = yield redis.zrangebyscore( SET_LIMIT_FELLOW_NAME_SCORE, 60, '+inf' )
        for _name in _names:
            _cid = yield redis.hget(DICT_NICKNAME_REGISTERED, str(_name))
            if _cid:
                yield g_AwardCenterMgr.new_award( _cid, AWARD_TYPE_LIMIT_FELLOW_SCORE, [int(time()), activity_id, 0] )

    yield redis.delete( HASH_LIMIT_FELLOW_SHRINE, SET_LIMIT_FELLOW_NAME_SCORE )


@defer.inlineCallbacks
def check_limit_fellow(deleted=False):
    ''' 开服期间的限时神将活动
    @param: deleted-True:清除旧数据, False:不清除
    '''
    global ACTIVITY_AWARD_TIME

    _all_excite_conf = get_excite_activity_conf()
    for _excite_conf in _all_excite_conf.itervalues():
        if _excite_conf['ActivityID'] == EXCITE_LIMIT_FELLOW:
            break
    else:
        yield redis.delete( HASH_LIMIT_FELLOW_SHRINE, SET_LIMIT_FELLOW_NAME_SCORE )
        defer.returnValue( None )
    # 限时神将 每次OSS同步会删除旧的数据 
    if deleted:
        yield redis.delete( HASH_LIMIT_FELLOW_SHRINE, SET_LIMIT_FELLOW_NAME_SCORE )

    # 限时神将中开启的活动配置
    _activity = get_limit_fellow_conf()
    if not _activity:
        yield redis.delete( HASH_LIMIT_FELLOW_SHRINE, SET_LIMIT_FELLOW_NAME_SCORE )
        defer.returnValue( None )

    _activity_id = _activity['ActivityID']
    # 限时神将 活动的奖励
    _award_conf  = get_limit_fellow_award_conf( _activity_id )
    if not _award_conf:
        yield redis.delete( HASH_LIMIT_FELLOW_SHRINE, SET_LIMIT_FELLOW_NAME_SCORE )
        defer.returnValue( None )

    # 定时
    all_ranks = _award_conf.keys()
    ACTIVITY_AWARD_TIME = int(time())
    interval_seconds = datetime2time( _excite_conf['CloseTime'] ) - ACTIVITY_AWARD_TIME
    if interval_seconds <= 0:
        defer.returnValue( None )

    log.warn('limit fellow would award to award center after {0} seconds, _activity_id: {1}, ACTIVITY_AWARD_TIME: {2}.'.format( interval_seconds, _activity_id, ACTIVITY_AWARD_TIME ))
    reactor.callLater( interval_seconds, grant_limit_fellow_award, all_ranks, _activity_id, ACTIVITY_AWARD_TIME )
    defer.returnValue( None )


try:
    ACTIVITY_AWARD_TIME
except:
    ACTIVITY_AWARD_TIME = int(time())


