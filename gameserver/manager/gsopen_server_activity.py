#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Song Huang <huangxiaohen2738@gmail.com>
# License: Copyright(c) 2015 Song.Huang
# Summary: 

from twisted.internet       import defer

from time     import mktime, strptime, time
from datetime import date, timedelta, datetime
from marshal  import loads, dumps
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from models.item            import *
from system   import get_open_server_quest_conf, get_open_server_shop_conf


class OpenServerActivityMgr(object):
    def __init__(self, user):
        self.cid = user.cid
        self.user = user

    def get_after_day_timestamp(self, n):
        timeArray = date.today() + timedelta(days = n)
        timeArray = strptime(str(timeArray), "%Y-%m-%d")
        timeStamp = int(mktime(timeArray))
        return timeStamp
    
    def get_quest_id_by_day(self, day):
        dic = {}
        _conf = get_open_server_quest_conf().get(1, {})
        l = _conf.keys()
        l.sort()
        for i in xrange(1,8):
            if i == 7 :
                dic[i] = [l[i-1], l[i]]
            else:
                dic[i] = l[i-1]

        return dic[day]

    @defer.inlineCallbacks
    def get_open_server_activity_status(self):
        '''获取活动状态
            time1:活动结束时间，time2:领取结束时间
            return [time1, time2, res1, res2, res3]
        '''
        _streams = yield redis.hget(HASH_OPEN_SERVER_INFO, "end_time")
        res = []
        if _streams:
            dayDict, active_end_time, active_get_time = loads(_streams) 
            if int(time()) >= active_get_time:
                defer.returnValue(OPEN_SERVER_IS_CLOSED)
        else:
            dayDict = {}
            active_end_time, active_get_time = self.get_after_day_timestamp(7), self.get_after_day_timestamp(10)
            for i in xrange(1,8):
                if i == 1:
                    dayDict[i] = time()
                else:
                    dayDict[i] = self.get_after_day_timestamp(i-1)
            yield redis.hset(HASH_OPEN_SERVER_INFO, "end_time", dumps([dayDict, active_end_time, active_get_time]))

        _stream = yield redis.hget(HASH_OPEN_SERVER_INFO, self.cid)
        if _stream:
            _data, _shop_data = loads(_stream)
            for i in xrange(1, 8):
                if int(time()) >= dayDict[i] and _shop_data[i] == 0:
                    _shop_data[i] = 1
                
                q_id = self.get_quest_id_by_day(i)
                if i == 7:
                    p, q = q_id
                    if int(time()) >= dayDict[i] and _data[1][p][0] == 0:
                        _data[1][p][0] = 1
                    if int(time()) >= dayDict[i] and _data[1][q][0] == 0:
                        _data[1][q][0] = 1
                else:
                    if int(time()) >= dayDict[i] and _data[1][q_id][0] == 0:
                        _data[1][q_id][0] = 1

                yield redis.hset(HASH_OPEN_SERVER_INFO, self.cid, dumps([_data, _shop_data]))
        else:
            _data = {}
            _shop_data = {}
            quest_info = get_open_server_quest_conf()
            if quest_info:
                for acType, info in quest_info.iteritems():
                    if acType == OPEN_SERVER_SHOP:
                        continue
                    for quest_id, value in info.iteritems():
                        status = 1 if quest_id == self.get_quest_id_by_day(1) else 0
                        if _data.has_key(acType):
                            _data[acType][quest_id] = [status, 0]
                        else:
                            _data[acType] = {quest_id:[status,0]}
            shop_info = get_open_server_shop_conf()
            if shop_info:
                for day, _ in shop_info.iteritems():
                    if day == 1:
                        _shop_data[day] = 1
                        continue
                    _shop_data[day] = 0

            yield redis.hset(HASH_OPEN_SERVER_INFO, self.cid, dumps([_data, _shop_data]))
        _info = yield redis.hget(HASH_OPEN_SERVER_INFO, "server_shop_count")
        if _info:
            buy_count = loads(_info)
        else:
            buy_count = [0] * 7 
            yield redis.hset(HASH_OPEN_SERVER_INFO, "server_shop_count", dumps(buy_count))
        
        _res1 = []
        if _data is not None:
            for _, _datas in _data.iteritems():
                for _id, _v in _datas.iteritems():
                    _res1.append([_id, _v[0], _v[1]])
        _res2 = []
        if _shop_data is not None:
            for _k, _v in _shop_data.iteritems():
                _res2.append([_k, _v])
        res = [active_end_time, active_get_time, _res1, _res2, buy_count]
        defer.returnValue( res )
    
    @defer.inlineCallbacks
    def buy_open_server_item(self, acType, quest_id):
        '''领取或购买
        acType 类别,任务类型，0为商店
        quest_id, 唯一id
        '''
        if not self.check_open_time(flag=True):
            defer.returnValue(OPEN_SERVER_IS_CLOSED)
        #shop
        if acType == OPEN_SERVER_SHOP:
            _conf = get_open_server_shop_conf(quest_id) 
            if not _conf:
                defer.returnValue(OPEN_SERVER_QUEST_IS_NOT_EXISTED)
            _type, _id, _num = _conf['ItemType'], _conf['ItemID'], _conf['ItemNum']
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                defer.returnValue(UNKNOWN_ITEM_ERROR)
            _streams = yield redis.hget(HASH_OPEN_SERVER_INFO, "server_shop_count")
            buy_count = 0
            if _streams:
                _data = loads(_streams)
                if _data[quest_id-1] >=_conf['ServerCount']:
                    defer.returnValue(OPEN_SERVER_SHOP_NUM_MAX)
                _data[quest_id-1] += 1
                buy_count = _data[quest_id-1]
                yield redis.hset(HASH_OPEN_SERVER_INFO, "server_shop_count", dumps(_data))
        
            _stream = yield redis.hget(HASH_OPEN_SERVER_INFO, self.cid)
            if _stream:
                _info, _data = loads(_stream)
                if _data[quest_id] != 1:
                    defer.returnValue( OPEN_SERVER_SHOP_HAD_BUY )
                _data[quest_id] = 2
                yield redis.hset(HASH_OPEN_SERVER_INFO, self.cid, dumps([_info, _data]))

            if _type == 1:
                res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_OPEN_SERVER_ACTIVITY_BUY, CapacityFlag=False)
                yield self.user.consume_credits(_conf['PresentPrice'], WAY_OPEN_SERVER_ACTIVITY_BUY)
            else:
                res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_OPEN_SERVER_ACTIVITY_BUY, CapacityFlag=False, CostCredits= _conf['PresentPrice'])
            defer.returnValue([2, buy_count, self.user.credits, [value[0]] ])
        #quest
        elif acType in OPEN_SERVER_QUEST_LIST:
            res = []
            _all_conf = get_open_server_quest_conf(acType, quest_id)
            if _all_conf:
                value, reward = _all_conf
            else:
                defer.returnValue(OPEN_SERVER_QUEST_IS_NOT_EXISTED)
            _stream = yield redis.hget(HASH_OPEN_SERVER_INFO, self.cid)
            if _stream:
                _info, _data, = loads(_stream)
                status, _v = _info.get(acType, 0).get(quest_id, 0)
                if status == 1 :
                    for _conf in reward:
                        _type, _id, _num = _conf[0], _conf[1], _conf[2]
                        model = ITEM_MODELs.get( _type, None )
                        if not model:
                            log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                            defer.returnValue(UNKNOWN_ITEM_ERROR)
                        res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_OPEN_SERVER_ACTIVITY_GOT, CapacityFlag=False)
                        res.append(value[0])
                    _info[acType][quest_id] = [2, _v]
                    yield redis.hset(HASH_OPEN_SERVER_INFO, self.cid, dumps([_info, _data]))
                    defer.returnValue([2, _v, self.user.credits, res])
                else:
                    defer.returnValue( OPEN_SERVER_QUEST_WRONG )
        
        else:
            defer.returnValue( OPEN_SERVER_KIND_WRONG )
    
    @defer.inlineCallbacks
    def check_open_time(self, flag=False):
        _stream = yield redis.hget(HASH_OPEN_SERVER_INFO, "end_time")
        if not _stream:
            dayDict = {}
            active_end_time, active_get_time = self.get_after_day_timestamp(7), self.get_after_day_timestamp(10)
            for i in xrange(1,8):
                if i == 1:
                    dayDict[i] = int(time())
                else:
                    dayDict[i] = self.get_after_day_timestamp(i-1)
            yield redis.hset(HASH_OPEN_SERVER_INFO, "end_time", dumps([dayDict, active_end_time, active_get_time]))
            defer.returnValue(False)
        
        start_time, end_time, end_get_time = loads(_stream)
        if not flag:
            if int(time()) <= end_time:
                defer.returnValue(True)
            defer.returnValue(False)
        if int(time()) <= end_get_time:
            defer.returnValue(True)
        defer.returnValue(False)

    @defer.inlineCallbacks
    def update_open_server_activity_quest(self, acType, count):
        ''' 更新开服狂欢任务的状态信息 
        '''
        ret = yield self.check_open_time()
        if not ret:
            defer.returnValue(OPEN_SERVER_IS_CLOSED)
        #获取任务状态
        data = yield redis.hget(HASH_OPEN_SERVER_INFO, self.cid)
        if not data:
            defer.returnValue( None )
        _data, _shop_data = loads( data )
    
        _all_conf = get_open_server_quest_conf()
        if not _all_conf:
            defer.returnValue( NOT_FOUND_CONF )
        #获取任务配置
        _value_data = _all_conf.get(acType, {})

        #修改任务完成进度和状态
        for _id, _v in _data.get(acType, {}).iteritems():
            if not _value_data.has_key(_id):
                continue
            if _v[0] == 1 or _v[0] == 2:
                continue
            _target_value = _value_data.get(_id, [0])[0]
            if acType in [OPEN_SERVER_QUEST_ID_3,OPEN_SERVER_QUEST_ID_10,OPEN_SERVER_QUEST_ID_2, OPEN_SERVER_QUEST_ID_4, OPEN_SERVER_QUEST_ID_11, OPEN_SERVER_QUEST_ID_12, OPEN_SERVER_QUEST_ID_14]:
                #玩家等级,混沌,战斗力,副本，精英, 天外天
                if int(count) >= _target_value and _v[0] == 0:
                    _v[0] = 1
                _v[1] = count
            elif acType in [OPEN_SERVER_QUEST_ID_5, OPEN_SERVER_QUEST_ID_6]:
                #穿戴装备品质, 强化装备
                if count[_target_value] >= 24 and _v[0] == 0:
                    _v[0] = 1
                _v[1] = count[_target_value]
            elif acType == OPEN_SERVER_QUEST_ID_7:
                #决斗场排名
                if int(count)!=0 and int(count) <= _target_value and _v[0] == 0:
                    _v[0] = 1
                _v[1] = count
            elif acType in [OPEN_SERVER_QUEST_ID_8, OPEN_SERVER_QUEST_ID_9,  
                            OPEN_SERVER_QUEST_ID_13, OPEN_SERVER_QUEST_ID_15, OPEN_SERVER_QUEST_ID_16]: 
                _v[1] += count
                if _target_value <= _v[1] and _v[0] == 0:
                    _v[0] = 1
            else:
                break
        
        # 更新任务状态
        yield redis.hset(HASH_OPEN_SERVER_INFO, self.cid, dumps([_data, _shop_data]))

        defer.returnValue( NO_ERROR )

