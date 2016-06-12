#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Song.huang<huangxiaohen2738@gmail.com>
# License: Copyright(c) 2015 Ethon.Huang
# Summary: 

from twisted.internet       import defer

from time     import time
from marshal  import loads, dumps
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from utils    import get_reset_timestamp
from system   import get_all_achievement_conf

from models.item            import *
    
#副本,玩家等级,混沌,精英,战斗力,天外天, vipLevel,好友数量，
#上阵伙伴数量,神将好感总等级,仙盟等级,玉魄种类,装备种类,宝物种类,伙伴最高等级
#宝物精炼,上阵伙伴装备精炼Level
ACHIEVEMENT_TYPE_1 = [ACHIEVEMENT_QUEST_ID_3, ACHIEVEMENT_QUEST_ID_4, ACHIEVEMENT_QUEST_ID_10,
                    ACHIEVEMENT_QUEST_ID_11, ACHIEVEMENT_QUEST_ID_12, 
                    ACHIEVEMENT_QUEST_ID_14, ACHIEVEMENT_QUEST_ID_18,
                    ACHIEVEMENT_QUEST_ID_20, ACHIEVEMENT_QUEST_ID_22, ACHIEVEMENT_QUEST_ID_23,
                    ACHIEVEMENT_QUEST_ID_24, ACHIEVEMENT_QUEST_ID_28, ACHIEVEMENT_QUEST_ID_33]

ACHIEVEMENT_TYPE_2 = [ACHIEVEMENT_QUEST_ID_8, ACHIEVEMENT_QUEST_ID_9,  
                    ACHIEVEMENT_QUEST_ID_13, ACHIEVEMENT_QUEST_ID_15, 
                    ACHIEVEMENT_QUEST_ID_16, ACHIEVEMENT_QUEST_ID_21,
                    ACHIEVEMENT_QUEST_ID_29,
                    ACHIEVEMENT_QUEST_ID_30, ACHIEVEMENT_QUEST_ID_31,
                    ACHIEVEMENT_QUEST_ID_32]

class GSAchievementMgr(object):
    def __init__(self, user):
        self.cid  = user.cid
        self.user = user


    @defer.inlineCallbacks
    def status(self):
        ''' 获取玩家的成就当前的状态, 含奖励和任务进度
        return [[_id, status, value],..]
        redis: actype:{_id:(status,value)}
        '''
        res_err = self.user.check_function_open(FUNCTION_ACHIEVEMENT)
        if res_err:
            defer.returnValue( res_err )

        data = yield redis.hget(HASH_ACHIEVEMENT_INFO, self.cid)
        res = []
        if not data:
            _all_conf = get_all_achievement_conf()
            _d = {}
            if _all_conf:
                for acType, _info in _all_conf.iteritems():
                    for _id, _v in _info.iteritems():
                        status = 0
                        if _d.has_key(acType):
                            _d[acType][_id] = [status, 0]
                        else:
                            _d[acType] = {_id:[status,0]}
                        res.append([_id, 0, 0])

                yield redis.hset(HASH_ACHIEVEMENT_INFO, self.cid, dumps(_d))
            defer.returnValue( res )
            
        _data = loads( data )
        res = yield self.sync_old_record(_data)

        defer.returnValue( res )

    @defer.inlineCallbacks
    def update_alliance_level(self):
        _s = yield redis.hget(HASH_ALLIANCE_INFO, self.user.alliance_id)
        if _s:
            d = loads(_s)
            level = d[2]
            self.update_achievement_status(24, level)

    @defer.inlineCallbacks
    def update_achievement_status(self, quest_type, count):
        ''' 更新成就的状态信息 
        @param: quest_type-成就type, count-完成数量
        '''
        res_err = self.user.check_function_open(FUNCTION_ACHIEVEMENT)
        if res_err:
            defer.returnValue( res_err )

        _all_conf = get_all_achievement_conf()
        if not _all_conf:
            defer.returnValue( NOT_FOUND_CONF )

        _conf = _all_conf.get( quest_type, None )
        #type:{id:(value, pid, reward)}
        if not _conf:
            defer.returnValue( UNKNOWN_ACHIEVEMENT_TYPE )

        #update alliance level
        all_level = yield self.update_alliance_level()

        _stream = yield redis.hget(HASH_ACHIEVEMENT_INFO, self.cid)
        _dic = {}
        if not _stream:
            for acType, _info in _all_conf.iteritems():
                for _id, _v in _info.iteritems():
                    status = 0
                    if _dic.has_key(acType):
                        _dic[acType][_id] = [status, 0]
                    else:
                        _dic[acType] = {_id:[status,0]}

            yield redis.hset(HASH_ACHIEVEMENT_INFO, self.cid, dumps(_dic))
        _data = loads(_stream) if _stream else _dic
        sorted(_data[quest_type].keys())
        for _id, _v in _data[quest_type].iteritems():
            if not _conf.has_key(_id):
                continue
            _target_value, _pid, _ = _conf[_id]
            if _v[0] == 1 or _v[0] == 2:
                 continue
            if quest_type in ACHIEVEMENT_TYPE_1:                
                if int(count) >= _target_value and _v[0] == 0:
                    if _pid != 0 and _data[quest_type].get(_pid, [0])[0] == 0:
                        pass
                    else:
                        _v[0] = 1
                _v[1] = max(_v[1], count)
            elif quest_type in [ACHIEVEMENT_QUEST_ID_7, ACHIEVEMENT_QUEST_ID_19]:
                    #角斗场排名, 大乱斗
                if int(count) !=0 and int(count) <= _target_value and _v[0] == 0:
                    if _pid != 0 and _data[quest_type].get(_pid, [0])[0] == 0:
                        pass
                    else:
                        _v[0] = 1
                _v[1] = min(_v[1], count)
            elif quest_type in ACHIEVEMENT_TYPE_2: 
                _v[1] += count
                if _v[1] >= _target_value and _v[0] == 0:
                    if _pid != 0 and _data[quest_type].get(_pid, [0])[0] == 0:
                        pass
                    else:
                        _v[0] = 1
           # elif quest_type in [ACHIEVEMENT_QUEST_ID_5, ACHIEVEMENT_QUEST_ID_6]:
           #     #穿戴装备品质,强化装备
           #     if count[_target_value] >= 24 and _v[0] == 0:
           #         _v[0] = 1
           #     _v[1] = count[_target_value]
            else:
                defer.returnValue(UNKNOWN_ACHIEVEMENT_TYPE)

        yield redis.hset( HASH_ACHIEVEMENT_INFO, self.cid, dumps(_data) )

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def sync_old_record(self, data):
        _all_conf = get_all_achievement_conf()
        if not _all_conf:
            defer.returnValue( NOT_FOUND_CONF )
        for quest_type, _info in data.iteritems():
            _f = sorted(_info.items())
            for _id, _v in _f:
                if not _all_conf.get(quest_type, {}).has_key(_id):
                    continue
                _target_value, _pid, _ = _all_conf[quest_type][_id]
                if int(_pid) != 0 and int(_info.get(int(_pid), [0])[0]) == 0:
                    continue
                if _v[0] == 1 or _v[0] == 2:
                    continue
                if quest_type in (ACHIEVEMENT_TYPE_1 + ACHIEVEMENT_TYPE_2):                
                    if int(_v[1]) >= int(_target_value) and int(_v[0]) == 0:
                        _info[_id][0] = 1
                elif quest_type in [ACHIEVEMENT_QUEST_ID_7, ACHIEVEMENT_QUEST_ID_19]:
                    #角斗场排名, 大乱斗
                    if int(_v[1]!=0) and int(_v[1]) <= int(_target_value) and _v[0] == 0:
                        _info[_id][0] = 1
            #    elif quest_type in ACHIEVEMENT_TYPE_2: 
            #        if _v[1] >= int(_target_value) and int(_v[0]) == 0:
            #            _v[0] = 1

        yield redis.hset(HASH_ACHIEVEMENT_INFO, self.cid, dumps(data))
        res = []
        for _type, _info in data.iteritems():
            for _id, value in _info.iteritems():
                res.append([_id, value[0], value[1]])

        defer.returnValue(res)


    @defer.inlineCallbacks
    def get_reward(self, quest_type, quest_id):
        res_err = self.user.check_function_open(FUNCTION_ACHIEVEMENT)
        if res_err:
            defer.returnValue( res_err )

        _data = yield redis.hget(HASH_ACHIEVEMENT_INFO, self.cid)
        if not _data:
            defer.returnValue(ACHIEVEMENT_HAS_NOT_FINISH)
        data = loads(_data)
        _all_conf = get_all_achievement_conf()
        if not _all_conf:
            defer.returnValue( NOT_FOUND_CONF )

        _conf = _all_conf.get(quest_type, {}).get(quest_id, {})
        #value, pre_id, reward
        if not _conf:
            defer.returnValue( NOT_FOUND_CONF )
        if _conf[1] != 0:
            #检查前置任务是否完成
            status, value = data.get(quest_type, {}).get(_conf[1], [])
            if status == 0:
                defer.returnValue(PREVIOUS_ACHIEVEMENT_NOT_FINISH)

        _st, _value = data[quest_type][quest_id]
        if _st != 1:
            #检查任务是否完成
            defer.returnValue(ACHIEVEMENT_HAS_NOT_FINISH)
        data[quest_type][quest_id] = [2, _value]
        yield redis.hset(HASH_ACHIEVEMENT_INFO, self.cid, dumps(data))
        _res = []
        for _type, _id, _num in _conf[2]:
            model = ITEM_MODELs.get( int(_type), None )
            if not model:
                log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                defer.returnValue(UNKNOWN_ITEM_ERROR)
            res_err, value = yield model(self.user, ItemID= int(_id), ItemNum= int(_num), AddType=WAY_ACHIEVEMENT, CapacityFlag=False)
            _res.append(value[0])

        defer.returnValue( _res )

