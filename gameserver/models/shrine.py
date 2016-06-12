#!/usr/bin/env python
#-*-coding: utf-8-*-

#from twisted.internet import defer
#from protocol_manager import cs_call
#
#from time     import time
#from log      import log   
#from errorno  import *
#from constant import *
#from redis    import redis
#from marshal  import loads, dumps     
#from system   import get_randcard_consume_conf, get_randcard_level_count, get_randcard_max_level
#
#
#class RandCardShrine(object):    
#    def __init__(self, cid, card_type, level=0, rand_count=0, rand_time=0):
#        self.cid            = cid
#        self.card_type      = card_type
#        self.level          = level
#        self.rand_count     = rand_count
#        self.last_rand_time = rand_time
#
#    @defer.inlineCallbacks
#    def sync(self):
#        yield redis.hset( DICT_SHRINE_STATUS % self.card_type, self.cid, dumps((self.level, self.rand_count, self.last_rand_time)) )
#
#    @defer.inlineCallbacks
#    @staticmethod
#    def load(character_id, card_type):
#        _data = yield redis.hget(DICT_SHRINE_STATUS % card_type, character_id)
#
#        if _data:
#            _level, _rand_cnt, _last_rand_time = loads( _data )
#
#            _self = RandCardShrine(character_id, card_type, _level, _rand_cnt, _last_rand_time)
#        else:
#            #time_now = int(time())
#            yield redis.hset( DICT_SHRINE_STATUS % card_type, character_id, dumps((0, 0, 0)) )
#            _self = RandCardShrine(character_id, card_type)
#
#        return _self
#
#    def add(self, free_timestamp):
#        _levelup      = False
#        _max_level    = get_randcard_max_level( self.card_type )
#
#        _next_level   = self.level + 1
#        _next_level   = _next_level if _next_level < _max_level else _max_level
#        _next_max_cnt = get_randcard_level_count(_next_level, self.card_type)
#        self.rand_count += 1
#        _cur_time = int(time())
#        if self.card_type == CARD_SHRINE_PURPLE and (_cur_time - self.last_rand_time) > free_timestamp:
#            self.last_rand_time = int(time())
#        elif self.card_type == CARD_SHRINE_BLUE and (_cur_time - self.last_rand_time) > free_timestamp:
#            self.last_rand_time = int(time())
#
#        if self.rand_count > _next_max_cnt:
#            # 神坛已升级到最高等级
#            if self.level >= _max_level:
#                self.rand_count = 0
#            else:
#                if _next_max_cnt:
#                    self.level      = _next_level
#                    self.rand_count = 0
#                    _levelup        = True
#        yield redis.hset(DICT_SHRINE_STATUS % self.card_type, self.cid, dumps((self.level, self.rand_count, self.last_rand_time)))
#
#        return _levelup
#
#    @property
#    def free_timestamp_left(self):
#        _conf = get_randcard_consume_conf(self.card_type)
#        _left_time = -1
#        if _conf:
#            _free_time = _conf['FreeTime']
#            if self.last_rand_time:
#                _left_time = int(self.last_rand_time + _free_time - time())
#                if _left_time < 0:
#                    _left_time = 0
#            else:
#                _left_time = -1 # _free_time
#
#        return _left_time
#
#    @property
#    def rand_count_left(self):
#        _max_level    = get_randcard_max_level( self.card_type )
#        _next_level   = self.level + 1
#        _next_level   = _next_level if _next_level < _max_level else _max_level
#        _next_max_cnt = get_randcard_level_count(_next_level, self.card_type)
#        if _next_max_cnt < self.rand_count:
#            log.error('rand_count_left. Shrine level error. card_type: {0}, shrine_level: {1}, rand_count: {2}.'.format( self.card_type, self.level, self.rand_count ))
#            _count_left = 0
#        else:
#            _count_left = _next_max_cnt - self.rand_count
#
#        return _count_left


