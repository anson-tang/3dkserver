#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2015 Don.Li
# Summary: 

from twisted.internet import reactor, defer

from system   import sysconfig
from redis    import redis
from time     import time
from datetime import datetime
from log      import log
from errorno  import *
from constant import *
from utils    import rand_num

from models.award_center import g_AwardCenterMgr
from protocol_manager    import gw_broadcast_cids, alli_call, gw_send, gw_broadcast
from manager.gsuser   import g_UserMgr

from marshal  import loads, dumps

def get_worldboss_attribute(level):
    return sysconfig['worldboss_attribute'].get(int(level), None)

def get_worldboss_reward(rank):
    _all = sysconfig['worldboss_reward']
    _all_keys = _all.keys()
    _all_keys.sort()

    _conf = None

    for _rank in _all_keys:
        if _rank > rank:
            break
        _conf = _all[_rank]
    else:
        _conf = _all[_all_keys[-1]]

    return _conf

WORLDBOSS_MAX_LEVEL = 0
def get_worldboss_maxlevel():
    global WORLDBOSS_MAX_LEVEL

    if not WORLDBOSS_MAX_LEVEL:
        _allconf = sysconfig['worldboss_attribute']
        WORLDBOSS_MAX_LEVEL = max(_allconf.keys())

    return WORLDBOSS_MAX_LEVEL

ATTACK_EXTRA_MAX_LEVEL = 0
def get_attack_extra_maxlevel():
    global ATTACK_EXTRA_MAX_LEVEL

    _allconf = sysconfig['worldboss_inspire']

    if not ATTACK_EXTRA_MAX_LEVEL:
        ATTACK_EXTRA_MAX_LEVEL = max(_allconf.keys())

    return ATTACK_EXTRA_MAX_LEVEL

def get_attack_extra_by_level(level):
    return sysconfig['worldboss_inspire'].get(int(level), None)

def get_current_level(last_level, damage_total):
    _level = 1

    if damage_total >= 0: #不是第一次
        _conf = get_worldboss_attribute(last_level)
        if _conf:
            _life = _conf['Life']
            if damage_total < _life and last_level > 1:
                _level = last_level - 1
            elif damage_total >= _life and last_level < get_worldboss_maxlevel():
                _level = last_level + 1
        else:
            log.error('no worldboss attribute config for level:{0}.'.format(last_level))

    return _level

DEFAULT_DURATION = (10, 0, 0), (19, 0, 0)
#DEFAULT_DURATION = (21, 0, 0), (21, 15, 0)
ATTACK_CD        = 60
BOOST_EXTRA_PER_LEVEL = 5

class AttackerData(object):
    _cache = {}

    def __init__(self, cid):
        self._cid = cid

        self._attack_count       = 0 #当前攻击次数
        self._damage_total = 0
        self._attack_time  = 0
        self._clear_count  = 0 #当前复活(清除CD)次数

        self._gold_inspire_failed_count   = 0 #金币鼓舞失败次数
        self._credit_inspire_failed_count = 0 #点劵鼓舞失败次数

        self._gold_inspire_success_count   = 0 #金币鼓舞成功次数
        self._credit_inspire_success_count = 0 #点劵鼓舞失败次数

    @staticmethod
    @defer.inlineCallbacks
    def get(cid):
        _data = None

        if worldBoss.running:
            _data = AttackerData._cache.get(cid, None)

            if not _data:
                _data = yield AttackerData.load(cid)

                if _data:
                    AttackerData._cache[cid] = _data
                    worldBoss.add_attacker(cid)

        defer.returnValue(_data)

    @staticmethod
    @defer.inlineCallbacks
    def load(cid):
        _stream = yield redis.hget(DICT_WORLDBOSS_ATTACKER_DATA, cid)

        _attacker = AttackerData(cid)

        if _stream:
            _data = loads(_stream)
            
            _attacker._attack_count, _attacker._damage_total, _attacker._attack_time, _attacker._clear_count, \
                    _attacker._gold_inspire_failed_count, _attacker._credit_inspire_failed_count,\
                    _attacker._gold_inspire_success_count, _attacker._credit_inspire_success_count = _data
        else:
            _attacker.sync()

        defer.returnValue(_attacker)

    @property
    def attack_extra_level(self): #当前鼓舞等级
        return self._gold_inspire_success_count + self._credit_inspire_success_count

    def sync(self):
        redis.hset(DICT_WORLDBOSS_ATTACKER_DATA, self._cid, 
                dumps((self._attack_count, self._damage_total, self._attack_time, self._clear_count,
                    self._gold_inspire_failed_count, self._credit_inspire_failed_count,
                    self._gold_inspire_success_count, self._credit_inspire_success_count)))

    @property
    @defer.inlineCallbacks
    def rank(self):
        _rank = yield redis.zrank(RANK_WORLDBOSS_DAMAGE, self._cid)

        if not _rank:
            yield redis.zadd(RANK_WORLDBOSS_DAMAGE, self._cid, -self._damage_total)
            _rank = yield redis.zrank(RANK_WORLDBOSS_DAMAGE, self._cid)

        defer.returnValue(_rank)

    @property
    @defer.inlineCallbacks
    def value(self):
        if worldBoss.running:
            if self._attack_count > 0:
                _rank = yield self.rank
            else:
                _rank = -1

            _w_damage_total = worldBoss._damage_total
            _percent = int(float(self._damage_total) * 10000 / _w_damage_total) if _w_damage_total else 0

            defer.returnValue((self._attack_count, int(self._attack_time), self._damage_total, _percent, 
                self._gold_inspire_success_count, self._credit_inspire_success_count, self._clear_count, _rank + 1))

    @defer.inlineCallbacks
    def attack(self, user, damage):
        _now = time()

        if self._attack_time:
            if (_now - self._attack_time) < ATTACK_CD:
                log.warn('[ attack ]CD time. last attack time:{0}, now:{1}.', self._attack_time, _now)
                defer.returnValue((WORLDBOSS_CD, None))

        _current_life = worldBoss.life
        if _current_life <= 0:
            defer.returnValue((WORLDBOSS_DEAD_ALREADY, None))

        self._attack_count += 1

        '''
        转到客户端算
        _attack_extra = self._attack_extra_level * 5
        damage = int(int(damage) * (100 + _attack_extra) / 100)
        '''
        self._damage_total += damage

        _farm = 10
        user.base_att.prestige += _farm

        worldBoss.on_attack(self._cid, user.nick_name, damage)

        self._attack_time  = _now

        self.sync()

        yield redis.zadd(RANK_WORLDBOSS_DAMAGE, self._cid, -self._damage_total)
        yield redis.hset(DICT_WORLDBOSS_RANKER_DATA, self._cid, dumps((user.nick_name, user.level, user.alliance_id)))

        #log.debug('attack come here...', self, self.__dict__)
        _current_rank = yield self.rank
        defer.returnValue((NO_ERROR, (self._damage_total, _farm, worldBoss.life, _current_rank+1)))

    def clear_cd(self, user):
        _cost = 10 * (1 + self._clear_count)

        if user.credits < _cost:
            return CHAR_CREDIT_NOT_ENOUGH
        else:
            self._clear_count += 1
            self._attack_time = 0

            user.consume_credits(_cost, WAY_WORLDBOSS_CLEAR_CD)
            self.sync()

            return NO_ERROR

    def boost(self, user, boost_type): #type: 1:gold, 2:credit
        _max_level  = get_attack_extra_maxlevel()
        _next_level = 1
        _conf       = None

        if self.attack_extra_level >= _max_level:
            return WORLDBOSS_INSPIRE_MAX_LEVEL_REACHED

        if boost_type == 1:
            _field_rate     = 'GoldRate'
            _field_add_rate = 'GoldAddRate'
            _field_cost     = 'GoldCost'
            _failed_count   = self._gold_inspire_failed_count

            _next_level = self._gold_inspire_success_count + 1
            _conf = get_attack_extra_by_level(_next_level)
        elif boost_type == 2:
            _field_rate     = 'CreditsRate'
            _field_add_rate = 'CreditsAddRate'
            _field_cost     = 'CreditsCost'
            _failed_count   = self._credit_inspire_failed_count

            _next_level = self._credit_inspire_success_count + 1
            _conf = get_attack_extra_by_level(_next_level)
        else:
            log.error('no boost type:', boost_type, 'cid:', self._cid)
            return UNKNOWN_ERROR

        if _conf:
            _rate, _add_rate, _cost = _conf[_field_rate], _conf[_field_add_rate], _conf[_field_cost]

            if (boost_type == 1 and _cost > user.golds):
                return CHAR_GOLD_NOT_ENOUGH
            elif (boost_type == 2 and _cost > user.credits):
                return CHAR_CREDIT_NOT_ENOUGH

            _rand = rand_num()
            if _rand <= _rate + _add_rate * _failed_count:
                self._gold_inspire_failed_count = self._credit_inspire_failed_count = 0
                #self._attack_extra_level = _next_level

                if boost_type == 1:
                    self._gold_inspire_success_count = _next_level
                    user.consume_golds(_cost, WAY_WORLDBOSS_BOOST)
                elif boost_type == 2:
                    self._credit_inspire_success_count = _next_level
                    user.consume_credits(_cost, WAY_WORLDBOSS_BOOST)
            else:
                if boost_type == 1:
                    self._gold_inspire_failed_count += 1
                elif boost_type == 2:
                    self._credit_inspire_failed_count += 1

            self.sync()

            return NO_ERROR
        else:
            log.error('no attack extra config for level:', _next_level, 'current level:', self.attack_extra_level, 'cid:', self._cid)
            return WORLDBOSS_NO_INSPIRE_CONFIG

    def reward(self, life, reward_golds, reward_farm, last_kill_golds, last_kill_fame, last_attacker_name, rank):
        gw_send(self._cid, 'sync_damage_report', (life, (last_attacker_name, self._damage_total, rank + 1, reward_golds, reward_farm, last_kill_golds, last_kill_fame)))

class WorldBoss(object):
    def __init__(self):
        self._duration           = DEFAULT_DURATION
        self._level              = 1
        self._char_names_last    = []
        self._char_name_lastkill = ''

        self._damage_total       = 0
        self._damage_char_list   = []

        self._running            = False
        self._finished           = False #当天是否已结束
        self._attackers          = [] #正在活动页面的玩家cid列表
        self._last_attackers     = [] #最后10位攻击过魔主的玩家信息，格式：[(nickname, damage), ...]

        self._cached_rank        = []

        self._last_rank_time     = 0
        self._max_life           = 0

    @property
    def running(self):
        return self._running

    def is_running(self):
        running = False

        _n_hour, _n_min, _n_sec = datetime.now().timetuple()[3:6]
        if _n_hour == 0 and _n_sec == 0 and _n_sec == 0: #第二天重置
            self._finished = False

        if not self._finished and self._duration:
            (_b_hour, _b_min, _b_sec), (_e_hour, _e_min, _e_sec) = self._duration

            if (_n_hour < _b_hour or _n_hour > _e_hour): return running 

            if _n_hour == _b_hour:
                if _n_min < _b_min: return running
                if _n_min == _b_min:
                    if _n_sec < _b_sec: return running

            if _n_hour == _e_hour:
                if _n_min > _e_min: return running
                if _n_min == _e_min:
                    if _n_sec > _e_sec: return running

            running = True

        return running

    @defer.inlineCallbacks
    def init(self):
        _stream = yield redis.get(DICT_WORLDBOSS_INFO)

        if not _stream:
            self._level = 1
            self._char_names_last    = []
            self._char_name_lastkill = ''
            self._damage_total       = 0
            self._duration           = DEFAULT_DURATION
            self._running            = False
            self._finished           = False
        else:
            try:
                _conf = loads(_stream)
            except:
                log.exception("_stream: {0}".format(_stream))
            else:
                try:
                    self._level              = _conf[0]
                    self._char_names_last    = _conf[1]
                    self._char_name_lastkill = _conf[2]
                    self._damage_total       = _conf[3]
                    self._duration           = _conf[4]
                    self._running            = _conf[5]
                    self._max_life           = int(get_worldboss_attribute(self._level)['Life'])
                except:
                    log.exception("_conf: {0}".format(_conf))

        if not self._running:
            self.update()
        else:
            reactor.callLater(1, self.update)

        reactor.addSystemEventTrigger('before', 'shutdown', self.sync)
        log.info('world boss status Loaded.')

    @defer.inlineCallbacks
    def sync(self):
        _conf = self._level, self._char_names_last, self._char_name_lastkill, self._damage_total, self._duration, self._running
        yield redis.set(DICT_WORLDBOSS_INFO, dumps(_conf))
        log.info('world boss status saved.')

    @property
    def value(self):
        if self._running:
            return None
        else:
            return self._char_names_last, self._char_name_lastkill

    def update_duration(self, new_duration):
        if self._running:
            log.error('worldboss  is running. only can update when it closed. current duration:', self._duration)
            return 10025
        else:
            self._duration = new_duration
            log.info('worldboss duration have been updated. current duration:', self._duration)
            return 1

    @property
    def life(self):
        if not self._running:
            return 0
        else:
            return int(self._max_life - self._damage_total)

    @defer.inlineCallbacks
    def close(self):
        _last_attacker_id, _last_attacker_name = 0, ''
        if self._last_attackers and self.life <= 0:
            _last_attacker_id, _last_attacker_name = self._last_attackers[-1][:2]

        _cids = yield redis.zrange(RANK_WORLDBOSS_DAMAGE, 0, 3)
        if not _cids: defer.returnValue(None) #没有一个人杀Boss，不算拉拉拉

        _dict_char_info = yield redis.hmget(DICT_WORLDBOSS_RANKER_DATA, _cids)
        self._char_names_last = [loads(_info)[0] for _info in _dict_char_info if _info]
        _len = len(self._char_names_last)
        if _len < 3:
            for x in xrange(3 - _len):
                self._char_names_last.append('')

        #log.warn('[ ddd ]:_cids:', _cids, '_dict_char_info:', _dict_char_info, '_len:', _len, '_char_names_last:', self._char_names_last)

        for _cid, _attacker in AttackerData._cache.iteritems():
            if _attacker._attack_count > 0:
                _rank = yield _attacker.rank
                reward_golds, reward_farm, last_kill_golds, last_kill_fame = self.reward_to_char(_cid, _last_attacker_id, _rank + 1)

                if _cid in self._attackers:
                    _attacker.reward(self.life, reward_golds, reward_farm, last_kill_golds, last_kill_fame, _last_attacker_name, _rank)

        self._char_name_lastkill = _last_attacker_name

        self.sync()
        res = yield self.current_rank()
        if res != []:
            first_user = g_UserMgr.getUser(res[0][0])
            if first_user:
                msg = [11, [first_user.nick_name, first_user.lead_id]]
                gw_broadcast('sync_broadcast', [[3, msg]])

        log.info('[ CLOSED ]WorldBoss have finished. last kill:', (_last_attacker_id, _last_attacker_name), 'last attackers:', self._last_attackers)

    def reward_to_char(self, cid, last_attacker_id, rank):
        reward_golds, reward_farm, last_kill_golds, last_kill_fame = 0, 0, 0, 0

        _conf = get_worldboss_reward(rank)
        if _conf:
            #_golds_add, _farm_add = 0, 0
            reward_golds = _conf['Gold']
            reward_farm  = _conf['Prestige']

            #_golds_add += reward_golds
            #_farm_add  += reward_farm

            _reward_items = [
                    (ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, reward_golds),
                    (ITEM_TYPE_MONEY, ITEM_MONEY_PRESTIGE, reward_farm),
                ]

            _rand = rand_num()
            if _rand <= _conf['Rate']:
                _reward_items.extend(_conf['RandomItem'])

            g_AwardCenterMgr.new_award(cid, AWARD_TYPE_WORLDBOSS_RANK, [int(time()), _reward_items], True)

            if int(last_attacker_id) == int(cid):
                log.debug('[ reward_to_char ]: last_attacker_id:{0}, cid:{1}.'.format(last_attacker_id, cid))
                _last_kill_conf = get_worldboss_reward(0)

                last_kill_golds = _last_kill_conf['Gold']
                last_kill_fame  = _last_kill_conf['Prestige']

                _reward_items = [
                        (ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, last_kill_golds),
                        (ITEM_TYPE_MONEY, ITEM_MONEY_PRESTIGE, last_kill_fame)
                    ]

                _rand = rand_num()
                if _rand <= _last_kill_conf['Rate']:
                    _reward_items.extend(_last_kill_conf['RandomItem'])

                g_AwardCenterMgr.new_award(cid, AWARD_TYPE_WORLDBOSS_LASTKILL, [int(time()), _reward_items], True)

        return reward_golds, reward_farm, last_kill_golds, last_kill_fame

    def update(self):
        try:
            _isRunning = self.is_running()

            if self._running and (not _isRunning or self.life <= 0): #end
                self._running  = False
                self._finished = True
                self.close()

                log.info('world boss was gone... life:', self.life, 'duration:', self._duration)
            elif not self._running and _isRunning: #Begin
                self._level    = get_current_level(self._level, self._damage_total)
                self._max_life = int(get_worldboss_attribute(self._level)['Life'])

                self._char_names_last    = []
                self._char_name_lastkill = ""
                self._damage_total       = 0

                redis.delete(DICT_WORLDBOSS_ATTACKER_DATA)
                redis.delete(DICT_WORLDBOSS_RANKER_DATA)
                redis.delete(RANK_WORLDBOSS_DAMAGE)
                AttackerData._cache = {}

                self._cached_rank        = []

                self._running  = True
                self._finished = False

                log.info('world boss is coming... life:', self.life, 'duration:', self._duration)

            if self._running:
                self.broadcast()
        except:
            log.exception()

        reactor.callLater(1, self.update)

    def add_attacker(self, cid):
        cid = int( cid )
        if cid not in self._attackers:
            self._attackers.append(cid)

    def remove_attacker(self, cid):
        cid = int( cid )
        if cid in self._attackers:
            self._attackers.remove(cid)

    def on_attack(self, cid, nickname, damage):
        if len(self._last_attackers) >= 10: del self._last_attackers[0]
        self._last_attackers.append((cid, nickname, damage))

        self._damage_total += damage
        self.add_attacker(cid)

    def broadcast(self):
        if self._last_attackers:
            gw_broadcast_cids('worldboss_attacked_list_broadcast', (self.life, self._last_attackers), self._attackers)
            self._last_attackers = []

    @defer.inlineCallbacks
    def current_rank(self):
        if self._cached_rank: 
            if not self._running: #不在活动期间，直接返回缓存数据
                defer.returnValue(self._cached_rank)
            else:
                _now = time()
                if _now - self._last_rank_time <= 10:
                    defer.returnValue(self._cached_rank)
                else:
                    self._last_rank_time = _now

        _cids = yield redis.zrange(RANK_WORLDBOSS_DAMAGE, 0, 10, True)
        if _cids:
            _dict_char_info = yield redis.hmget(DICT_WORLDBOSS_RANKER_DATA, [r[0] for r in _cids])
        else:
            _dict_char_info = []

        #log.debug('_cids:', _cids, '_dict_char_info:', _dict_char_info)

        _res = []
        _alli_ids = []

        for idx, (cid, damage) in enumerate(_cids):
            _info = _dict_char_info[idx]
            if _info:
                _name, _level, _alliance_id = loads(_info)
                _alli_ids.append(_alliance_id)
                _res.append([cid, _name, _level, _alliance_id, -damage, idx + 1])
            else:
                log.error('No such user data in ranker data. cid:', cid)

        if _alli_ids:
            #从公会服务器以ID换取公会名
            _alli_names = yield alli_call('get_alliance_names', (_alli_ids,))
            for _idx, (_cid, _name) in enumerate(_alli_names):
                if _name:
                    _res[_idx][3] = _name
                else:
                    _res[_idx][3] = ''

            if not self._running:
                self._cached_rank = _res

        defer.returnValue(_res)

try:
    worldBoss
except NameError:
    worldBoss = WorldBoss()
