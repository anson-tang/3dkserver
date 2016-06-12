#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from time     import time
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps
from utils    import timestamp_is_today, rand_num

from twisted.internet       import defer
from system                 import get_exchange_limited_conf, get_exchange_refresh_conf, get_all_exchange_limited_conf
from models.item            import *

LOCK_TYPE_NONE     = 0
LOCK_TYPE_MATERIAL = 1
LOCK_TYPE_TARGET   = 2

EXCHANGE_TYPE_SHENJIANG = 1
EXCHANGE_TYPE_ZUOJI     = 2
EXCHANGE_TYPE_DIANJI    = 3


class GSExchangeLimitedMgr(object):
    def __init__(self, excite_activity_mgr, user):
        self.user = user
        self.cid  = user.cid

        self.excite_activity_mgr = excite_activity_mgr

        #[ [ _id, _title, _type, _reset_cnt, _last_reset_t, _exchanged_cnt, _last_exchange_t, _locked_type, _material_1, _material_2, _material_3, _target ] ]
        self.__list         = None
        self.__t_lastupdate = None

    @defer.inlineCallbacks
    def exchange_refresh_times(self):
        _cnt = 0

        _list = yield self.exchange_list(True)
        for _exchange in _list:
            reset_cnt, _last_reset_t = _exchange[3:5]

            if not reset_cnt or not timestamp_is_today( _last_reset_t ):
                _cnt += 1

        defer.returnValue( _cnt )

    @defer.inlineCallbacks
    def lock_exchange_material(self, exchange_id, lock_type):
        res = EXCHANGE_NOT_FOUND

        if not self.__list:
            yield self.exchange_list()

        for _exchange in self.__list:
            if _exchange[0] == int( exchange_id ):
                _conf = get_exchange_limited_conf( exchange_id )
                if not _conf:
                    defer.returnValue( res )

                res = [ self.user.credits ]

                if lock_type == LOCK_TYPE_MATERIAL:
                    _credits_need = _conf['MaterialLockedCost']
                elif lock_type == LOCK_TYPE_TARGET:
                    _credits_need = _conf['TargetLockedCost']
                else:
                    _exchange[7] = LOCK_TYPE_NONE
                    log.warn( 'unknown lock type:{0}. _exchange:{1}.'.format( lock_type, _exchange ) )
                    defer.returnValue( res )

                res_consume = yield self.user.consume_credits( _credits_need, WAY_LIMIT_EXCHANGE_LOCK )
                if res_consume:
                    res = res_consume
                    defer.returnValue( res )

                _exchange[7] = lock_type
                log.debug( 'lock type:{0}. _exchange:{1}, res:{2}.'.format( lock_type, _exchange, res ) )

                self.sync()

                res = [ self.user.credits ]
                break

        defer.returnValue( res )

    @defer.inlineCallbacks
    def refresh_exchange_material(self, exchange_id):
        res = EXCHANGE_NOT_FOUND
        #res = [ EXCHANGE_NOT_FOUND, 0, None ]

        if not self.__list:
            yield self.exchange_list()

        for _exchange in self.__list:
            if _exchange[0] == int( exchange_id ):
                reset_cnt, _last_reset_t = _exchange[3:5]

                if not timestamp_is_today( _last_reset_t ):
                    reset_cnt = 0

                _credits_need = 0

                if reset_cnt:
                    _conf = get_exchange_limited_conf( exchange_id )
                    if not _conf:
                        log.warn('not found exchange config. id:{0}'.format( exchange_id ))
                    else:
                        _credits_need = min( _conf['MaxCost'], _conf['ResetCost'] + ( reset_cnt - 1 ) * _conf['AddCost'] )
                        res_consume = yield self.user.consume_credits( _credits_need, WAY_LIMIT_EXCHANGE_REFRESH )

                        if res_consume:
                            defer.returnValue( res_consume )

                _materials = yield self.refresh_materials( _exchange[2], add_cnt = True, lock_type=_exchange[7], material_3=_exchange[10], target=_exchange[11] )
                _exchange[8], _exchange[9] = _materials[:2]
                _exchange[10] = _materials[2] or _exchange[10]
                _exchange[11] = _materials[3] or _exchange[11]

                _exchange[3] += 1                #更新当日刷新次数
                _exchange[4]  = int( time() )    #更新最后一次刷新时间戳

                self.sync()

                res = [ self.user.credits, [ _exchange[0], _exchange[1], _exchange[2], _exchange[3], _exchange[5] , _exchange[7], _exchange[8:] ] ]
                break

        defer.returnValue( res )


    @defer.inlineCallbacks
    def exchange_list(self, detail = False):
        '''
        @summary: 获取当前user可以兑换的兑换信息
        '''
        _list = []

        _begin_t, _end_t = self.excite_activity_mgr.open_and_close_time( EXCITE_EXCHANGE_LIMITED )
        if not (_begin_t and _end_t):
            log.error('unknown conf. begin t:{0}, end t:{1}.'.format( _begin_t, _end_t ))
            defer.returnValue( _list )

        if not self.__list:
            _data = yield redis.hget( HASH_EXCHANGE_LIMITED, self.cid )

            _n = int( time() )
            if _data:
                self.__t_lastupdate, _data = loads( _data )

                if self.__t_lastupdate < _begin_t or self.__t_lastupdate > _end_t:
                    _data = []
            else:
                self.__t_lastupdate = _n
                _data               = []

            _all_exchange_conf = get_all_exchange_limited_conf()

            for _conf in _all_exchange_conf.itervalues():
                _id, _title, _type = _conf['ExchangeID'], _conf['Title'], _conf['Type']
                _reset_cnt, _last_reset_t, _exchanged_cnt, _last_exchange_t, _locked_type = 0, _n, 0, _n, 0
                _material_1, _material_2, _material_3, _target = None, None, None, None

                for _haved in _data:
                    if _haved[0] == _id:
                        _reset_cnt, _last_reset_t, _exchanged_cnt, _last_exchange_t, _locked_type, _material_1, _material_2, _material_3, _target = _haved[3:]
                        if not timestamp_is_today( _last_reset_t ):
                            _reset_cnt = 0
                            _last_reset_t = _n
                        if not timestamp_is_today( _last_exchange_t ):
                            _exchanged_cnt = 0
                            _last_exchange_t = _n

                        break
                else:
                    _material_1, _material_2, _material_3, _target = yield self.refresh_materials( _type, False )

                #这个就是__list的数据结构了，找不到，就到这里来找
                _list.append( [ _id, _title, _type, _reset_cnt, _last_reset_t, _exchanged_cnt, _last_exchange_t, _locked_type, _material_1, _material_2, _material_3, _target ] )

            self.__list = _list
            self.sync()

        defer.returnValue( self.value(detail) )

    def sync( self ):
        self.__t_lastupdate = int( time() )
        redis.hset( HASH_EXCHANGE_LIMITED, self.cid, dumps( ( self.__t_lastupdate, self.__list ) ) )

    @defer.inlineCallbacks
    def __rand_material(self, exchange_type, turn, add_cnt, except_material = None ):
        _all_turns = get_exchange_refresh_conf( exchange_type, turn )

        _tmp_list_idx_and_rate = [] #暂存每个材料的index和计算出来的当前权重值

        _material   = None
        _rate_total = 0 #所有需要随机材料的总权重
        _curr_rate  = 0
        _rand       = 0

        if _all_turns:
            _all_turn_cnt = yield redis.hmget( HASH_EXCHANGE_REFRESH_RATE, [ '{0}.{1}'.format( self.cid, _conf[0] ) for _conf in _all_turns ] )
            _len_cnt = len( _all_turn_cnt )

            for _idx, _turn_conf in enumerate( _all_turns ):
                if except_material == [ _turn_conf[3], _turn_conf[4], _turn_conf[5] ]: # 该材料不能参与随机，防止材料重复, DK-1663
                    continue

                _cnt  = ( _all_turn_cnt[ _idx ] if _idx < _len_cnt else 0 ) or 0
                _rate = _turn_conf[6] + ( ( _cnt * _turn_conf[7] ) if _cnt else 0 )

                if _rate >= _turn_conf[8]:
                    _rate = _turn_conf[8]

                _tmp_list_idx_and_rate.append( [ _idx, _rate, _cnt ] )

                _rate_total += _rate

            _rand = rand_num( _rate_total )

            for _c_idx, _c_rate, _c_cnt in _tmp_list_idx_and_rate:
                if _rand <= _curr_rate + _c_rate: #hitted
                    _conf = _all_turns[ _c_idx ]

                    #这里是material和target的数据结构了，找不到来这里找
                    if not _material:
                        _material = [ _conf[3], _conf[4], _conf[5] ]

                    if add_cnt:
                        redis.hset( HASH_EXCHANGE_REFRESH_RATE, '{0}.{1}'.format( self.cid, _conf[0] ), 0 ) #命中后重置
                else:
                    if add_cnt:
                        redis.hset( HASH_EXCHANGE_REFRESH_RATE, '{0}.{1}'.format( self.cid, _conf[0] ), _c_cnt + 1 ) #miss后累加

                _curr_rate += _c_rate

        if not _material:
            log.warn( 'missing rand material. list_idx_and_rate as: {0}, exchange_type:{1}, turn:{2}, _all_turns:{3}, _curr_rate:{4}, _rate_total:{5}, _rand:{6}.'.format( 
                    _tmp_list_idx_and_rate, exchange_type, turn, _all_turns, _curr_rate, _rate_total, _rand ) )

        #log.debug( 'list_idx_and_rate as: {0}, exchange_type:{1}, turn:{2}, _all_turns:{3}, _curr_rate:{4}, _rate_total:{5}, _rand:{6}, _material:{7}.'.format( 
        #                _tmp_list_idx_and_rate, exchange_type, turn, _all_turns, _curr_rate, _rate_total, _rand, _material ) )

        defer.returnValue( _material )

    @defer.inlineCallbacks
    def refresh_materials(self, exchange_type, add_cnt=True, lock_type=LOCK_TYPE_NONE, material_3=None, target=None):
        _material_1, _material_2, _material_3, _target = None, None, None, None

        _turn = 0
        _material_1 = yield self.__rand_material( exchange_type, _turn, add_cnt )
        _turn = 1
        _material_2 = yield self.__rand_material( exchange_type, _turn, add_cnt )

        if lock_type != LOCK_TYPE_MATERIAL:
            _turn = 2
            _except_material = None
            if lock_type == LOCK_TYPE_TARGET:
                _except_material = target
            _material_3 = yield self.__rand_material( exchange_type, _turn, add_cnt, except_material=_except_material )

        if lock_type != LOCK_TYPE_TARGET:
            _turn = 3
            _except_material = _material_3
            if lock_type == LOCK_TYPE_MATERIAL:
                _except_material = material_3
            _target = yield self.__rand_material( exchange_type, _turn, add_cnt, except_material=_except_material )

        defer.returnValue( ( _material_1, _material_2, _material_3, _target ) )

    def value(self, detail):
        '''
        @summary: 当前兑换列表的数据
        '''
        #[ [ _id, _title, _type, _reset_cnt, _last_reset_t, _exchanged_cnt, _last_exchange_t, _locked_type, _material_1, _material_2, _material_3, _target ] ]
        if detail:
            return self.__list
        else:
            return [ item[:4] + item[5:6] + item[7:8] + [ item[8:] ] for item in self.__list ]


    @defer.inlineCallbacks
    def do_exchange(self, exchange_id ):
        res = EXCHANGE_NOT_FOUND

        if not self.__list:
            yield self.exchange_list()

        for _exchange in self.__list:
            if _exchange[0] == int( exchange_id ):
                _conf = get_exchange_limited_conf( exchange_id )
                if not _conf:
                    defer.returnValue( res )

                _exchanged_cnt, _last_exchange_t = _exchange[5:7]
                if not timestamp_is_today( _last_exchange_t ):
                    _exchanged_cnt = _exchange[5] = 0

                if _exchanged_cnt >= _conf['ExchangeNum']:
                    defer.returnValue( res )

                _material_1, _material_2, _material_3, _target = _exchange[8:12]
                err, _material_1_remain = yield item_use( self.user, ItemType=_material_1[0], ItemID=_material_1[1], ItemNum=_material_1[2] )
                if err:
                    log.error( 'do_exchange err:{0}, material:{1}.'.format( err, _material_1 ) )

                err, _material_2_remain = yield item_use( self.user, ItemType=_material_2[0], ItemID=_material_2[1], ItemNum=_material_2[2] )
                if err:
                    log.error( 'do_exchange err:{0}, material:{1}.'.format( err, _material_2 ) )

                err, _material_3_remain = yield item_use( self.user, ItemType=_material_3[0], ItemID=_material_3[1], ItemNum=_material_3[2], UseType=WAY_LIMIT_EXCHANGE )
                if err:
                    log.error( 'do_exchange err:{0}, material:{1}.'.format( err, _material_3 ) )

                err, _target_added = yield item_add( self.user, ItemType=_target[0], ItemID=_target[1], ItemNum=_target[2], AddType=WAY_LIMIT_EXCHANGE )

                res = err

                if not err:
                    _exchanged_cnt = _exchange[5] = _exchanged_cnt + 1
                    _exchange[6]   = int( time() )
                    _exchange[7]   = LOCK_TYPE_NONE  # 重置锁定

                    self.sync()
                    res = [ _exchanged_cnt, _material_1_remain, _material_2_remain, _material_3_remain, _target_added ]

                break

        defer.returnValue( res )
