#!/usr/bin/env python
#-*-coding: utf-8-*-

import sys

from twisted.internet import defer, reactor
from protocol_manager import cs_call
from twisted.internet.defer import inlineCallbacks, returnValue

from random   import sample
from time     import time
from log      import log   
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     

import sys

from utils       import timestamp_is_today, rand_num
from models.item import ITEM_MODELs, total_new_items
from system      import sysconfig

from models.award_center import g_AwardCenterMgr



STAR_POOL = xrange(1, 21)

class Constellation(object):
    def __init__(self, cid, score=0, select_count=0, hitted_count=0, free_count=0, select_time=0, stars_for_hit=None, stars_for_select=None, reward_time=0, rewards=None):
        self.cid              = cid
        self.score            = score
        self.select_count     = select_count
        self.free_count       = free_count
        self.hitted_count     = hitted_count

        self.stars_for_hit    = stars_for_hit
        self.stars_for_select = stars_for_select

        self.rewards          = rewards

        self.last_select_time = select_time
        self.last_reward_time = reward_time

        self.synced = False
        reactor.addSystemEventTrigger('before', 'shutdown', self.sync)

    @defer.inlineCallbacks
    def sync(self):
        if not self.synced:
            try:
                self.synced = True
                yield redis.hset( DICT_CONSTELLATION, self.cid, dumps( self.value_t ) )
                #log.debug('cid:{0} status saved. status:{1}.'.format(self.cid, self.value_t))
            except:
                log.exception('cid:{0} status save failed. status:{1}.'.format(self.cid, self.value_t))

    @property
    def free(self):
        return CONSTELLATION_FREE_REFRESH - self.free_count

    @property
    def need_refresh(self):
        ''' True-需要刷新 False-不需要刷新 '''
        if timestamp_is_today(self.last_select_time):
            return False
        else:
            return True

    @property
    def value(self):
        return self.stars_for_hit, self.stars_for_select, self.score, self.select_count, self.free, self.hitted_count

    @property
    def value_t(self):
        return self.stars_for_hit, self.stars_for_select, self.score, self.select_count, self.hitted_count, self.free_count, self.rewards, self.last_select_time, self.last_reward_time

    @staticmethod
    def rand_star_today( refresh=True, stars_for_hit=None ):
        stars4hit    = zip( sample( STAR_POOL, 4 ), (0, ) * 4 ) if refresh else stars_for_hit
        stars4select = sample( STAR_POOL, 5 )

        return stars4hit, stars4select

    @staticmethod
    def default_reward_today():
        return [ [ r[2], r[3], r[4], 0 ] for r in sysconfig['constellation_reward'] ]

    @staticmethod
    def stars_need(turn):
        res = sys.maxint

        all_base_rewards = sysconfig['constellation_reward']
        if turn < len( all_base_rewards ):
            res = all_base_rewards[ turn ][1]

        return res

    @staticmethod
    def score_extra(hitted_count):
        _conf = sysconfig['constellation_star']

        _turn = hitted_count + 1
        _len  = len(_conf)

        return _conf[_len]['ExtraStarNum'] if _turn >= _len else _conf[_turn]['ExtraStarNum']

    @staticmethod
    def rand_reward(turn):
        _all, _weight = sysconfig['constellation_reward_rand']

        _rewards  = _all.get(turn, None)
        _t_weight = _weight.get(turn, None)
        
        if _rewards and _t_weight:
            _tmp = 0
            _rand = rand_num(_t_weight)

            for reward in _rewards:
                _tmp += reward[3]
                if _rand <= _tmp:
                    return list(reward[:3])
            else:
                log.warn("[ Constellation.rand_reward ]missed, current tmp:{0}, rand:{1}, turn:{2}.".format(_tmp, _rand, turn))
        else:
            log.warn("[ Constellation.rand_reward ]no turn {0} in sysconfig, rewards:{1}, weight:{2}.".format(turn, _rewards, _t_weight))

    @staticmethod
    @defer.inlineCallbacks
    def load(character_id):
        _data    = yield redis.hget(DICT_CONSTELLATION, character_id)
        _changed = False

        if _data:
            try:
                _stars4hit, _stars4select, _score, _select_cnt, _hitted_cnt, _free_cnt, _rewards, _last_select_time, _last_reward_time = loads( _data )
            except:
                _stars4hit, _stars4select, _score, _select_cnt, _free_cnt, _rewards, _last_select_time, _last_reward_time = loads( _data )
                _hitted_cnt = 0
        else:
            _last_select_time = 0
            _last_reward_time = 0

        if not timestamp_is_today( _last_select_time):
            _stars4hit, _stars4select = Constellation.rand_star_today()
            _score                    = 0
            _free_cnt                 = 0
            _select_cnt               = 0
            _hitted_cnt               = 0
            _last_select_time         = int(time())

            _changed = True

        if not timestamp_is_today( _last_reward_time ):
            _rewards          = Constellation.default_reward_today()
            _last_reward_time = int(time())

            _changed = True

        _self = Constellation(character_id, _score, _select_cnt, _hitted_cnt, _free_cnt, _last_select_time, _stars4hit, _stars4select, _last_reward_time, _rewards)

        if _changed:
            _self.sync()

        defer.returnValue( _self )

    def select(self, star_id, is_highlight):
        _added    = 1
        _hitted   = 0
        _hit_curr = False

        _stars = []

        self.synced = False

        for _star_for_hit, _star_is_hitted in self.stars_for_hit:
            if _star_is_hitted:
                _hitted        += 1
            elif not _hit_curr and _star_for_hit == star_id:
                _star_is_hitted = 1
                _hitted        += 1
                _hit_curr       = True

            _stars.append( ( _star_for_hit, _star_is_hitted ) )

        if ( is_highlight == 0 and _hit_curr ) or ( is_highlight == 1 and not _hit_curr ): #客户端和服务器状态不一致
            log.error("[ select ]star_id:{0}, is_highlight:{1}, stars:{2}.".format( star_id, is_highlight, self.stars_for_hit ))
            return CONSTELLATION_STAR_SYNC_ERROR

        self.select_count += 1
        _added             = 1

        self.stars_for_hit = _stars

        #log.debug('[ test ]: hitted:', _hitted, 'total hitted:', self.hitted_count, 'stars_for_hit:', self.stars_for_hit)

        if _hitted >= len( self.stars_for_hit ):
            _added            +=  Constellation.score_extra( self.hitted_count )
            self.hitted_count += 1

        self.score        += _added

        self.stars_for_hit, self.stars_for_select = Constellation.rand_star_today( _hitted >= len(self.stars_for_hit), self.stars_for_hit )

        return self.stars_for_hit, self.stars_for_select, self.score, self.select_count, self.hitted_count

    @inlineCallbacks
    def refresh(self, user, use_item):
        res, data = UNKNOWN_ERROR, None
        guanxing = None

        self.synced = False

        if self.free > 0: #优先使用免费次数
            self.free_count += 1
            res = NO_ERROR
        elif use_item:
            res, item_used = yield user.bag_item_mgr.use( ITEM_GUANXINGLING, 1 )
            if item_used:
                _g = item_used[0]
                guanxing = _g.attrib_id, _g.item_id, _g.item_num, _g.item_type
        else:
            res = yield user.consume_credits( CONSTELLATION_CREDITS_FOR_FREE, WAY_CONSTELLATION_REFRESH )

        if not res:
            _, self.stars_for_select = Constellation.rand_star_today( False )
            res = NO_ERROR
            
            data = self.stars_for_select, self.free, user.credits, guanxing

        returnValue( ( res, data ) )

    @inlineCallbacks
    def refresh_rewards(self, user):
        res, data = UNKNOWN_ERROR, None

        #[ [ r[2], r[3], r[4], 0 ] for r in sysconfig['constellation_reward'] ]
        self.synced = False

        res = yield user.consume_credits( CONSTELLATION_CREDITS_FOR_REWARD, WAY_CONSTELLATION_AWARD_REFRESH )

        if not res:
            for idx, reward in enumerate(self.rewards):
                received = reward[3]

                if not received:
                    _turn = idx + 1
                    _reward_rand = Constellation.rand_reward( _turn )

                    if _reward_rand:
                        self.rewards[idx] = list(_reward_rand) + [ received ]

            res  = NO_ERROR
            data = user.credits, self.rewards

        defer.returnValue( (res, data) )

    @defer.inlineCallbacks
    def receive_reward(self, user):
        res, data = UNKNOWN_ERROR, None

        self.synced = False

        items_return = []
        for idx, reward in enumerate(self.rewards):
            received = reward[3]

            if not received:
                if self.score >= Constellation.stars_need( idx ):
                    _add_func = ITEM_MODELs.get(reward[0], None)

                    if _add_func:
                        res_err, res_value = yield _add_func( user, ItemID = reward[1], ItemNum = reward[2], AddType=WAY_CONSTELLATION_AWARD, CapacityFlag=False )
                        if not res_err:
                            for _v in res_value:
                                items_return = total_new_items(_v, items_return)
                        reward = list(reward)
                        reward[3] = 1
                        self.rewards[idx] = reward
                        res = NO_ERROR
                    else:
                        log.error('[ Constellation.receve_reward ]no such item type: {0}.', reward[0])
                else:
                    log.error('[ Constellation.receve_reward ]too few score. score:{0}, idx:{1}, stars need:{2}.', self.score, idx, Constellation.stars_need(idx))

                break
            else:
                res = CONSTELLATION_REWARD_RECEIVED

        data = self.rewards

        defer.returnValue( (res, data, items_return) )

    @defer.inlineCallbacks
    def onekey_receive_reward(self, user):
        res = CONSTELLATION_REWARD_RECEIVED

        self.synced = False

        items_return = []
        for idx, reward in enumerate(self.rewards):
            if reward[3]:
                continue

            if self.score >= Constellation.stars_need( idx ):
                _add_func = ITEM_MODELs.get(reward[0], None)

                if _add_func:
                    res_err, res_value = yield _add_func( user, ItemID = reward[1], ItemNum = reward[2], AddType=WAY_CONSTELLATION_AWARD, CapacityFlag=False )
                    if not res_err:
                        for _v in res_value:
                            items_return = total_new_items(_v, items_return)
                    reward = list(reward)
                    reward[3] = 1
                    self.rewards[idx] = reward
                    res = NO_ERROR
                else:
                    log.error('[ Constellation.receve_reward ]no such item type: {0}.', reward[0])
            else:
                log.warn('user too few score. cid:{0}, score:{1}, idx:{2}, stars need:{3}.'.format( user.cid, self.score, idx, Constellation.stars_need(idx)) )
                break

        defer.returnValue( (res, self.rewards, items_return) )

    @defer.inlineCallbacks
    def reward_to_center(self):
        ''' 0点时将未领奖励发放到领奖中心 '''
        items_list = []
        for idx, reward in enumerate(self.rewards):
            if reward[3]:
                continue
            if self.score >= Constellation.stars_need( idx ):
                items_list.append( reward[:3] )
                # 更新领奖状态
                reward[3] = 1
                self.rewards[idx] = reward
                self.synced = False

        if items_list:
            timestamp = int(time())
            yield g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_CONSTELLATION, [timestamp, items_list] )



