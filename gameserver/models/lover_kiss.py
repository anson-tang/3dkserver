#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time     import time
from datetime import datetime
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     
from utils    import split_items, get_reset_timestamp, rand_num, timestamp_is_today
from syslogger import syslogger
from math import floor
from twisted.internet       import defer
from models.item            import item_use, item_add
from protocol_manager       import gw_broadcast

from system import get_lover_kiss_conf ,get_lover_kiss_rate_conf, get_lover_kiss_reward_conf_by_type

LUXURY_TYPE = 1
NORMAL_TYPE = 0

class LoverKissMgr(object):
    def __init__(self, user, n_rose, b_rose, extra_r, opened_num, opened_t, got_reward, opened_list):
        self.user = user
        self.cid = user.cid
        self.normal_rose = n_rose #一般rose
        self.blue_rose = b_rose    #蓝色妖姬
        self.extra_blue_rose = extra_r  #额外蓝色妖姬
        self.big_reward = got_reward #本轮是否获得大奖
        self.opened_num = opened_num  #已经获得美女数
        self.last_opened_t = opened_t #上次获得时间
        self.synced = False
        self.opened_list = opened_list
        self.user.lover_kiss_mgr = self
        if len(self.opened_list) == 0:
            self.opened_list = [-1] * 20

    @staticmethod
    @defer.inlineCallbacks
    def get(user):
        _lover_kiss_mgr = getattr(user, 'lover_kiss_mgr', None)
        if not _lover_kiss_mgr:
            _lover_kiss_mgr = yield LoverKissMgr.load(user)

        if _lover_kiss_mgr:
            _lover_kiss_mgr.update()

        defer.returnValue(_lover_kiss_mgr)

    @staticmethod
    @defer.inlineCallbacks
    def load(user):
        _instance = None

        _stream = yield redis.hget(DICT_LOVER_KISS, user.cid)
        if not _stream:
            _instance = LoverKissMgr(user, 5, 0, 0, 0, int(time()), 0, [])
            defer.returnValue(_instance)
        try:
            _data = loads(_stream)
            if _data:
                _n_rose, _b_rose, _extra_r, _opened_num, _opened_t, _got_blue, opened_list = _data
                _instance = LoverKissMgr(user, _n_rose, _b_rose, _extra_r, _opened_num, _opened_t, _got_blue, opened_list)
        except:
            log.exception()

        defer.returnValue( _instance )

    def update(self):
        _n = int(time())
        if timestamp_is_today(self.last_opened_t):
            _hours_passed = int(floor((_n - self.last_opened_t) / 3600))
            if _hours_passed >= 1:
                if self.normal_rose + _hours_passed <= 5:
                    self.normal_rose += _hours_passed
                    self.last_opened_t += (_hours_passed * 3600)
                else:
                    self.normal_rose = 5
                    self.last_opened_t = _n
        else:
            self.reset()
            self.normal_rose = 5
            self.extra_blue_rose = 0
            self.last_opened_t = _n
        
        self.sync()

    def sync(self):
        if not self.synced:
            try:
                redis.hset( DICT_LOVER_KISS, self.cid, dumps( self.value ) )
            except:
                log.exception('cid:{0} status save failed. status:{1}.'.format(self.cid, self.value))

    @property
    @defer.inlineCallbacks
    def value_t(self):
        yield self.update_blue_rose()
        if self.opened_num == 20:
            self.reset()
        result = self.normal_rose, self.blue_rose, BLUE_ROSE_MAX_NUM - self.extra_blue_rose, self.last_opened_t, self.opened_list
        defer.returnValue( result )

    @property
    def value(self):
        return self.normal_rose, self.blue_rose, self.extra_blue_rose, self.opened_num, self.last_opened_t, self.big_reward, self.opened_list

    
    def rand_reward_by_type(self, reward_type):
        _all_conf = get_lover_kiss_reward_conf_by_type(reward_type)

        _total_rate = sum([_conf[2] for _conf in _all_conf])
        _rand = rand_num(_total_rate)

        _res     = None
        _current = 0
        for _conf in _all_conf:
            _res = _conf
            if _rand < (_current + _conf[2]):
                break
            else:
                _current += _conf[2]
        else:
            log.error('reward not existed!')

        return _res[4], _res[3], _res[5], _res[6]

    def check_touch(self, location, t_type):
        if self.opened_list[location] != -1:
            return False
        if t_type == 1:
            if self.normal_rose <= 0:
                return False
            self.normal_rose -= 1
        elif t_type == 2:
            if self.blue_rose <= 0:
                return False
            self.blue_rose -= 1
        
        _rand = rand_num()
        if _rand <= get_lover_kiss_rate_conf(t_type)['Rate']:
            return True
        return False

    @defer.inlineCallbacks
    def get_touch_reward(self, location):
        self.opened_num += 1
        
        rate = get_lover_kiss_conf(self.opened_num)['LuxuryRewardRate']
        _rand = rand_num()
        
        if _rand <= rate and self.big_reward == 0:
            reward = self.rand_reward_by_type(LUXURY_TYPE)
            self.big_reward = 1
        else:
            reward = self.rand_reward_by_type(NORMAL_TYPE)
        
        notice = reward[-1]
        if notice:
            message = [ACHIEVE_TYPE_LOVER_KISS, self.user.nick_name, reward[0]]
            gw_broadcast('sync_broadcast', [message])
        
        _item = yield item_add(self.user, ItemType = reward[1], ItemID = reward[0], ItemNum = reward[2], AddType = WAY_LOVER_KISS)
        
        self.opened_list[location] = _item[1][0][2]
        self.synced = False
        self.sync()
        defer.returnValue( [_item[1], self.opened_list, self.normal_rose, self.blue_rose, BLUE_ROSE_MAX_NUM - self.extra_blue_rose])
    
    def reset(self):
        self.opened_num = 0
        self.opened_list = [-1] * 20
        self.big_reward = 0

    def refresh_box(self):
        if self.user.credits >= 20:
            self.user.consume_credits(20, WAY_LOVER_KISS)
            self.reset()

    def check_activity(self):
        if self.normal_rose == 0 and self.blue_rose == 0:
            return True
        return False

    @defer.inlineCallbacks
    def update_blue_rose(self):
        pay_date = datetime.now().strftime("%Y-%m-%d")
        num = 0
        _data = yield redis.hget(HASH_DAILY_PAY_RECORD, pay_date)
        if _data:
            _data = loads(_data)
        else:
            _data = []
        for _conf in _data:
            if _conf[0] == self.cid:
                num = int(floor(_conf[1] / 20))
                break
        if num > 0:
            num = num - self.extra_blue_rose
        if num > 0:
            if self.extra_blue_rose + num < BLUE_ROSE_MAX_NUM:
                self.extra_blue_rose += num
                self.blue_rose += num
            else:
                left = BLUE_ROSE_MAX_NUM - self.extra_blue_rose
                self.extra_blue_rose = BLUE_ROSE_MAX_NUM
                self.blue_rose += left
            self.sync()

