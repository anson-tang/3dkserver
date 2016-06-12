#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

from twisted.internet       import defer

from time     import time
from marshal  import loads, dumps
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from utils    import get_reset_timestamp
from system   import get_daily_quest_reward_conf, get_all_daily_quest_conf, get_all_daily_quest_reward_conf 


from models.item            import *
from models.award_center    import g_AwardCenterMgr


class GSDailyQuestMgr(object):
    ''' 
    @summary: 任务进度和宝箱在每天24:00重置清零，可领但未领的奖励要发往领奖中心;
    '''
    def __init__(self, user):
        self.cid  = user.cid
        self.user = user

    @defer.inlineCallbacks
    def status(self):
        ''' 获取玩家的每日任务当前的状态, 含奖励和任务进度
        '''
        data = yield redis.hget(HASH_DAILY_QUEST, self.cid)
        if not data:
            defer.returnValue( [int(time()), [], [], 0] )
        _data = loads( data )
        # 判断时间是否已过刷新时间
        _reset_timestamp = get_reset_timestamp()
        # 计算已获得的总积分
        _score = self.calc_total_score( _data[2] )
        _data[3] = _score

        if _data[0] <= _reset_timestamp:
            yield self.reward_to_center( _score, _data[1] )
            yield redis.hdel( HASH_DAILY_QUEST, self.cid )
            defer.returnValue( [int(time()), [], [], 0] )

        defer.returnValue( _data )

    def calc_total_score(self, quest_info):
        ''' 计算已获得的总积分 '''
        _score = 0
        _all_conf = get_all_daily_quest_conf()
        if not _all_conf:
            return _score

        for _quest_id, _quest_status, _count in quest_info:
            _conf = _all_conf.get(_quest_id, {})
            if not _conf:
                continue
            # quest_status:任务状态, 0-未完成 1-已完成未领取 2-已领取
            if _quest_status == 2 or _count >= _conf['Requirements']:
                _score += _conf['Score']

        return _score
    @defer.inlineCallbacks
    def get_reward(self, reward_id):
        ''' 领取每日任务奖励 '''
        _reward_conf = get_daily_quest_reward_conf(reward_id)
        if not _reward_conf:
            defer.returnValue( NOT_FOUND_CONF )
        # 每日任务当前的状态
        _status = yield self.status()
        # 重复领取
        if reward_id in _status[1]:
            defer.returnValue( REPEAT_REWARD_ERROR )
        # 总积分不足
        if _reward_conf['Score'] > _status[3]:
            defer.returnValue( DAILY_QUEST_SCORE_NOT_ENOUGH )
        # 给奖励
        add_type  = WAY_DAILY_QUEST
        add_items = [] # 新增的玩家道具信息
        for _type, _id, _num in _reward_conf['Reward']:
            _model = ITEM_MODELs.get(_type, None)
            if not _model:
                log.error('Unknown item type. ItemType: {0}.'.format( _type ))
                continue
            res_err, value = yield _model(self.user, ItemID=_id, ItemNum=_num, CapacityFlag=False, AddType=add_type)
            if not res_err and value:
                for _v in value:
                    add_items = total_new_items( _v, add_items )
            else:
                log.error('User add items error. res_err: {0}, value: {1}.'.format( res_err, value ))
        # 更新领奖记录
        _status[1].append( reward_id )
        yield redis.hset( HASH_DAILY_QUEST, self.cid, dumps(_status) )

        defer.returnValue( add_items )

    @defer.inlineCallbacks
    def update_daily_quest(self, quest_id, count):
        ''' 更新每日任务的状态信息 
        @param: quest_id-任务ID
        '''
        res_err = self.user.check_function_open(FUNCTION_DAILY_QUEST)
        if res_err:
            defer.returnValue( res_err )

        _all_conf = get_all_daily_quest_conf()
        if not _all_conf:
            defer.returnValue( NOT_FOUND_CONF )

        _conf = _all_conf.get( quest_id, None )
        if not _conf:
            defer.returnValue( UNKNOWN_DAILY_QUEST_ID )

        # 每日任务当前的状态
        _status = yield self.status()
        for _quest in _status[2]:
            if _quest[0] == quest_id:
                # 已完成的任务直接返回
                if _quest[1]:
                    defer.returnValue( NO_ERROR )

                _quest[2] += count
                # 判断任务是否已完成
                if _quest[2] >= _conf['Requirements']:
                    _quest[1] = DAILY_QUEST_DONE
                break
        else:
            # 判断任务是否已完成
            if count >= _conf['Requirements']:
                _status[2].append( [quest_id, DAILY_QUEST_DONE, count] )
            else:
                _status[2].append( [quest_id, 0, count] )
        # 更新每日任务状态
        yield redis.hset( HASH_DAILY_QUEST, self.cid, dumps(_status) )

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def reward_to_center(self, score, had_reward):
        ''' 重置前将未领的奖励发放到领奖中心 
        @param: score-获得的总积分
        @param: had_reward-已领取奖励的档位ID
        '''
        _all_reward_conf = get_all_daily_quest_reward_conf()
        if not _all_reward_conf:
            defer.returnValue( NOT_FOUND_CONF )

        _reward_ids = [] # 可领还未领的档位ID列表
        for _id, _conf in _all_reward_conf.iteritems():
            # 该档位已领取
            if _id in had_reward:
                continue
            # 总积分不足
            if _conf['Score'] > score:
                continue
            _reward_ids.append( _id )

        if _reward_ids:
            timestamp = int(time())
            yield g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_DAILY_QUEST, [timestamp, _reward_ids] )


    @defer.inlineCallbacks
    def get_daily_quest_reward(self, quest_id):
        _data = yield redis.hget(HASH_DAILY_QUEST, self.cid)
        if not _data:
            defer.returnValue( DAILY_QUEST_SCORE_NOT_ENOUGH )
        data = loads(_data)
        for _info in data[2]:
            if _info[0] == quest_id and _info[1] == 1:
                _conf = get_all_daily_quest_conf().get(quest_id, None)
                if _conf is None:
                    defer.returnValue( UNKNOWN_DAILY_QUEST_ID )
                _type, _id, _num = _conf["RewardList"].split(":")
                model = ITEM_MODELs.get( int(_type), None )
                if not model:
                    log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                    defer.returnValue(UNKNOWN_ITEM_ERROR)
                res_err, value = yield model(self.user, ItemID= int(_id), ItemNum= int(_num), AddType=WAY_DAILY_QUEST, CapacityFlag=False)
                _score = self.calc_total_score( data[2] )
                _info[1] = 2
                yield redis.hset(HASH_DAILY_QUEST, self.cid, dumps(data))
                defer.returnValue( ([value[0]], _score) )

        defer.returnValue( DAILY_QUEST_SCORE_NOT_ENOUGH )



