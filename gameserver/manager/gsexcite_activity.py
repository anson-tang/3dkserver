#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from marshal  import loads, dumps
from time     import time
from datetime import datetime
from log      import log
from errorno  import *
from constant import *
from utils    import datetime2time, timestamp_is_today
from redis    import redis

from twisted.internet           import defer, reactor
from system                     import get_excite_activity_conf, get_pay_activity_conf, get_consume_activity_conf, get_vip_conf, get_group_buy_conf, get_group_buy_reward_list_conf, get_group_buy_count
from manager.gsmystical_shop    import GSMysticalShopMgr
from manager.gsexchange_limited import GSExchangeLimitedMgr
from manager.gslimit_fellow     import GSLimitFellowMgr
from models.award_center        import g_AwardCenterMgr
from models.newyear_package     import newYearPackage
from models.lover_kiss          import LoverKissMgr
from models.item                import *
from models.randpackage         import package_open
from protocol_manager           import gw_broadcast
#from models.timelimited_shop    import timeLimitedShop

FREE_DIG_PACAKGE = 90007
CREDITS_DIG_PACAKGE = 90008
DIG_MAX_COUNT = 1000

class GSExciteActivityMgr(object):
    def __init__(self, user):
        ''' 精彩活动 '''
        self.user = user
        self.cid  = user.cid
        self.mystical_shop_mgr    = GSMysticalShopMgr( user )
        self.exchange_limited_mgr = GSExchangeLimitedMgr( self, user )
        self.limit_fellow_mgr     = GSLimitFellowMgr( user )
        self.free_dig_count = get_vip_conf(self.user.vip_level)["FreeDigCount"]
        self.dig_total_count = 0
        self.last_dig_time = time()
        self.vipLevel = 0

    def open_and_close_time(self, activity_type):
        _conf = get_excite_activity_conf()

        _begin_t, _end_t = 0, 0

        for _c in _conf.itervalues():
            if _c['ActivityID'] == activity_type:
                _begin_t, _end_t = datetime2time(_c['OpenTime']), datetime2time(_c['CloseTime'])
                break

        return _begin_t, _end_t

    @defer.inlineCallbacks
    def activity_info(self):
        _data   = []
        _dt_now = datetime.now()
        _conf   = get_excite_activity_conf()
        for _c in _conf.itervalues():
            _status = []
            if _c['OpenTime'] > _dt_now or _c['CloseTime'] <= _dt_now:
                continue
            if _c['ActivityID'] == EXCITE_FIRSTPAY:
                # 已完成首充
                if self.user.base_att.firstpay > 0:
                    continue
            elif _c['ActivityID'] == EXCITE_EAT_PEACH:
                _s , _, _, _ = yield self.user.check_eat_peach_status( _dt_now )
                _status = [_s]
            elif _c['ActivityID'] == EXCITE_MYSTICALSHOP:
                _status = yield self.mystical_shop_mgr.mystical_status()
            elif _c['ActivityID'] == EXCITE_MONTHLY_CARD:
                _status = yield self.user.new_check_monthly_card_status(MONTHLY_CARD_NORMAL)
                _dual_status = yield self.user.new_check_monthly_card_status(MONTHLY_CARD_DUAL)
                _status.extend(_dual_status)
            elif _c['ActivityID'] == EXCITE_GROWTH_PLAN:
                _s = yield self.user.check_growth_plan_status()
                # 奖励已领完
                _status = [_s]
            elif _c['ActivityID'] == EXCITE_EXCHANGE_LIMITED:
                _s = yield self.exchange_limited_mgr.exchange_refresh_times()
                _status = [ 1 if _s > 0 else 0]
            #elif _c['ActivityID'] == EXCITE_VIP_WELFARE:
            #    _s = yield self.user.check_vip_welfare_status()
                # 当前等级没有VIP福利
            #    if _s == 2:
            #        continue
            #    _status = [_s]
            elif _c['ActivityID'] == EXCITE_LIMIT_FELLOW:
                _s, _ = yield self.limit_fellow_mgr.status()
                if _s < 0:
                    continue
                _status = [_s]
            elif _c['ActivityID'] == EXCITE_PAY_ACTIVITY:
                _s, _total_pay = yield self.user.check_pay_activity_status()
                _status = [_total_pay, _s]
            elif _c['ActivityID'] == EXCITE_CONSUME_ACTIVITY:
                _s, _total_consume = yield self.user.check_consume_activity_status()
                _status = [_total_consume, _s]
            elif _c['ActivityID'] == EXCITE_NEWYEAR_PACKAGE:
                _recved = yield newYearPackage.received_today(self.user.cid)
                _s = 0 if _recved else 1
                _status = [_s]
            elif _c['ActivityID'] == EXCITE_LOVER_KISS:
                _m = yield LoverKissMgr.get(self.user)
                if _m:
                    _s = 0 if _m.check_activity() else 1
                    _status = [_s]
            elif _c['ActivityID'] == EXCITE_HAPPY_NEW_YEAR:
                _s = 0 if self.check_happy_new_year() == 0 else 1
                _status = [_s]
            elif _c['ActivityID'] == EXCITE_PAY_CREDITS_BACK:
                _had_back = yield self.user.pay_credits_back_status()
                _status   = [_had_back]
            elif _c['ActivityID'] == EXCITE_DIG_TREASURE:
                _s = yield self.get_dig_treasure_info()
                _status = [_s, self.free_dig_count, self.dig_total_count]
            elif _c['ActivityID'] == EXCITE_TIME_LIMIT_SHOP:
                #_can_buy = yield timeLimitedShop.can_buy(self.user)
                #_status = [_can_buy]
                _status = [1]
            _data.append( [_c['ID'], _c['ActivityID'], _c['ActivityType'], _c['ActivityName'], _c['ActivityIcon'], datetime2time(_c['OpenTime']), datetime2time(_c['CloseTime']), _status] )
        defer.returnValue( _data )

    def mystical_info(self, refresh_type):
        ''' 获取神秘商店的刷新次数、道具等信息 '''
        return self.mystical_shop_mgr.mystical_info( refresh_type )

    def exchange_mystical_item(self, index, item_type, item_id):
        ''' 兑换神秘商店的道具 '''
        return self.mystical_shop_mgr.exchange_item( index, item_type, item_id )

    def exchange_limited_list(self):
        return self.exchange_limited_mgr.exchange_list()

    @defer.inlineCallbacks
    def check_happy_new_year(self):
        ok = 1
        for item_id in HAPPY_NEW_YEAR:
            try:
                num, attr = yield self.user.bag_item_mgr.get_items(item_id)
            except:
                print 'num is not enough!'
            else:
                if num < 1:
                    ok = 0
                    break
        defer.returnValue(ok)

    @defer.inlineCallbacks
    def exchange_happy_new_year(self):
        left_list = []
        flag = yield self.check_happy_new_year()
        if flag == 1:
            for item_id in HAPPY_NEW_YEAR:
                res = yield item_use_normal_item(self.user, ItemType = ITEM_TYPE_CHEST, ItemID = item_id, ItemNum = 1)
                num, attr = yield self.user.bag_item_mgr.get_items(item_id)
                left = (res[1][0][0],res[1][0][1], res[1][0][2], num)
                left_list.append(left)
        
            _item = yield item_add_normal_item(self.user, ItemType = ITEM_TYPE_CHEST, ItemID = HAPPY_NEW_YEAR_PACKAGE, ItemNum = 1, AddType = WAY_HAPPY_NEW_YEAR)
            defer.returnValue( (left_list, _item[1]))
        defer.returnValue( ([], []))

    @defer.inlineCallbacks
    def get_dig_treasure_info(self):
        flag = 0
        _stream = yield redis.hget(DICT_DIG_TREASURE_INFO, self.cid)
        if _stream:
            try:
                _data = loads(_stream)
                if _data:
                    self.free_dig_count, self.dig_total_count, self.last_dig_time = _data
                    if not timestamp_is_today(self.last_dig_time):
                        self.free_dig_count = get_vip_conf(self.user.vip_level)["FreeDigCount"]
                        self.vipLevel = self.user.vip_level
                        self.last_dig_time = time()
                        _value = (self.free_dig_count, self.dig_total_count, self.last_dig_time)
                        yield redis.hset(DICT_DIG_TREASURE_INFO, self.cid, dumps(_value))
                    else:
                        if self.user.vip_level > self.vipLevel:
                            count = get_vip_conf(self.user.vip_level)["FreeDigCount"] - get_vip_conf(self.vipLevel)["FreeDigCount"]
                            self.free_dig_count += count
                            self.vipLevel = self.user.vip_level
                            _value = (self.free_dig_count, self.dig_total_count, self.last_dig_time)
                            yield redis.hset(DICT_DIG_TREASURE_INFO, self.cid, dumps(_value))

            except:
                log.exception()
        else:
            self.free_dig_count = get_vip_conf(self.user.vip_level)["FreeDigCount"]
            self.dig_total_count = 0
            self.last_dig_time = time()
            self.vipLevel = self.user.vip_level
            _value = (self.free_dig_count, self.dig_total_count, self.last_dig_time)
            yield redis.hset(DICT_DIG_TREASURE_INFO, self.cid, dumps(_value))
        if self.free_dig_count > 0:
            flag = 1
        defer.returnValue(flag)

    @defer.inlineCallbacks
    def get_dig_treasure_reward(self, t_type, count):
        if t_type == FREE_DIG:
            if self.free_dig_count >= 1:
                self.free_dig_count -= 1
                self.dig_total_count += 1
                self.last_dig_time = time()
                _value = (self.free_dig_count, self.dig_total_count, self.last_dig_time)
                yield redis.hset(DICT_DIG_TREASURE_INFO, self.cid, dumps(_value))
                _item_rand = yield package_open(self.user, FREE_DIG_PACAKGE)
                if _item_rand:
                    user_item_id = 0
                    _item_type, _item_id, _item_num, _notice = _item_rand
                    _res = yield item_add(self.user, ItemType=_item_type, ItemID=_item_id, ItemNum=_item_num, AddType=WAY_DIG_TREASURE_FREE)
                    defer.returnValue((_res[1], self.free_dig_count, self.dig_total_count, self.user.credits))
        elif t_type == CREDITS_DIG:
            if self.user.credits >= 20 * count and self.dig_total_count <DIG_MAX_COUNT :
                _itemList = []
                for i in xrange(count):
                    _item_rand = yield package_open(self.user, CREDITS_DIG_PACAKGE)
                    if _item_rand:
                        user_item_id = 0
                        _item_type, _item_id, _item_num, _notice = _item_rand
                        _res = yield item_add(self.user, ItemType=_item_type, ItemID=_item_id, ItemNum = _item_num, AddType=WAY_DIG_TREASURE_CREDITS)
                        _itemList.append(_res[1][0])
                    self.dig_total_count += 1
                    yield self.user.consume_credits(20, WAY_DIG_TREASURE_CREDITS)
                    self.last_dig_time = time()
                    _value = (self.free_dig_count, self.dig_total_count, self.last_dig_time)
                    yield redis.hset(DICT_DIG_TREASURE_INFO, self.cid, dumps(_value))
                    if self.dig_total_count >= DIG_MAX_COUNT :
                        break
                defer.returnValue((_itemList, self.free_dig_count, self.dig_total_count, self.user.credits))
            else:
                defer.returnValue(HAD_DIG_MAX_COUNT)

    @defer.inlineCallbacks
    def get_group_buy_info(self):
        _infos = yield redis.hgetall(DICT_GROUP_BUY_INFO)
        if not _infos:
            _group_buy_info = {1:0,2:0,3:0,4:0}  #buy_type:buy_num
            for buy_type in xrange(1,5):
                yield redis.hset(DICT_GROUP_BUY_INFO, buy_type, dumps(_group_buy_info[buy_type]))
        else:
            _group_buy_info = dict()
            for k, v in _infos.iteritems():
                _group_buy_info[k] = loads(v)

        _res = []
        _ret = []
        for _buy_type, _bought_num in _group_buy_info.iteritems():
           _res.append([_buy_type, _bought_num])

        _stream = yield redis.hget(DICT_GROUP_BUY_PERSON_INFO, self.cid)#[[buy_count, [status,2,3,4]],..]
        if _stream:
            try:
                _data = loads(_stream)
                if _data:
                    # [bought_count, [0,0,0,0]]
                    for _bought_count_info, _info in zip(_data, _res):
                        _info.append(_bought_count_info)
                        _ret.append(_info)
            except:
                log.exception()
        else:
            _value = [[0,[0,0,0,0]]] * 4
            yield redis.hset(DICT_GROUP_BUY_PERSON_INFO, self.cid, dumps(_value))
            for _info in _res:
                _info.append([0,[0,0,0,0]])
                _ret.append(_info)
        defer.returnValue( _ret )

    @defer.inlineCallbacks
    def buy_group_package(self, buy_type):
        if buy_type not in get_group_buy_conf().keys():
            defer.returnValue( BUY_GROUP_TYPE_WRONG )
        _conf = get_group_buy_conf(buy_type)
        _stream = yield redis.hget(DICT_GROUP_BUY_PERSON_INFO, self.cid)
        _data = loads(_stream)
        #[[buy_count, [0,0,0,0]], ......]
        bought_count, _info = _data[buy_type-1]
        if bought_count + 1 > _conf["LimitNum"]:
            defer.returnValue(GROUP_BUY_MAX_COUNT)
        if self.user.credits < _conf["CurrentPrice"]:
            defer.returnValue(CHAR_CREDIT_NOT_ENOUGH)
        yield self.user.consume_credits(_conf["CurrentPrice"], WAY_GROUP_BUY)
        bought_count +=1
        _st = yield redis.hget(DICT_GROUP_BUY_INFO, buy_type)
        _datas = loads(_st)
        #buy_type:buy_num
        _total_buy_count = _datas
        if bought_count == 1:
            _total_buy_count += 1
        _data[buy_type-1] = [bought_count, _info]
        yield redis.hset(DICT_GROUP_BUY_PERSON_INFO, self.cid, dumps(_data))
        yield redis.hset(DICT_GROUP_BUY_INFO, buy_type, dumps(_total_buy_count))
        _item_type, _item_id, _item_num = _conf['ItemType'], _conf['ItemID'], _conf['ItemNum']
        _res = yield item_add(self.user, ItemType=_item_type, ItemID=_item_id, ItemNum = _item_num, AddType=WAY_GROUP_BUY)
        _result = (buy_type, _total_buy_count, bought_count, _res[1][0], self.user.credits)
        defer.returnValue( _result )
    
    @defer.inlineCallbacks
    def get_group_buy_reward(self, buy_type, buy_count):
        if buy_type not in get_group_buy_conf().keys() or buy_count not in get_group_buy_count():
            defer.returnValue( BUY_GROUP_TYPE_WRONG )
        _wlist = list(set(get_group_buy_count()))
        _st = yield redis.hget(DICT_GROUP_BUY_INFO, buy_type)
        #buy_type:buy_num
        _data = loads(_st)
        _count = _data
        if _count < buy_count:
            defer.returnValue( BUY_NUM_NOT_ENOUGH )
        _stream = yield redis.hget(DICT_GROUP_BUY_PERSON_INFO, self.cid)
        _info = loads(_stream)
        #[[buy_count,[status,,,]],...]
        _buy_count, _get_info = _info[buy_type-1]
        if _buy_count <= 0:
            defer.returnValue( BUY_STATUS_IS_WRONG )
        _index = _wlist.index(buy_count)
        if _get_info[_index] == 1:
            defer.returnValue( BUY_STATUS_IS_WRONG)
        _get_info[_index] = 1
        _info[buy_type-1] = [_buy_count, _get_info]
        _reward = get_group_buy_reward_list_conf(buy_type, buy_count)      
        _item_type, _item_id, _item_num = _reward.split(":")
        _res = yield item_add(self.user, ItemType= int(_item_type), ItemID= int(_item_id), ItemNum = int(_item_num), AddType=WAY_GROUP_BUY)
        yield redis.hset(DICT_GROUP_BUY_PERSON_INFO, self.cid, dumps(_info))
        defer.returnValue((buy_type, buy_count, _res[1][0]))

@defer.inlineCallbacks
def grant_group_buy_award(activity_id, redis_key, award_center_type, timestamp=0):
    log.warn('excite activity award. activity_id: {0}, timestamp: {1}, GROUP_BUY_AWRAD_TIME: {2}.'.format( activity_id, timestamp,
        GROUP_BUY_AWARD_TIME))

    _field = None
    _award_conf = None
    if GROUP_BUY_AWARD_TIME != timestamp:
        defer.returnValue( None )
    if activity_id != EXCITE_GROUP_BUY:
        defer.returnValue( None )
    _all_data = yield redis.hgetall( redis_key )
    if not _all_data:
        defer.returnValue( None )
    _group_buy_info = yield redis.hgetall( DICT_GROUP_BUY_INFO )
    _wlist = list(set(get_group_buy_count())) #buy_num level
    _gdict = dict()
    #save group_buy activity buy_num
    for k, v in _group_buy_info.iteritems():
        _gdict[k] = loads(v)

    for _cid, _data in _all_data.iteritems():
        _data = loads(_data)
        _args_list = []
        for _index, (_count, _status) in enumerate(_data):
            if _count <= 0:
                break
            _award_ids = []
            for dex, i in enumerate(_status):
                if i == 1 or dex in _award_ids:
                    continue
                if _gdict[_index+1] >= _wlist[_index] and i == 0:
                    _args_list.append([_index+1, _wlist[_index+1]])
                    _award_ids.append(dex)
        if len(_args_list) >= 1:
            yield g_AwardCenterMgr.new_award( _cid, award_center_type, [int(time()), activity_id, _args_list] )

    yield redis.delete( redis_key )
    yield redis.delete( DICT_GROUP_BUY_INFO )

@defer.inlineCallbacks
def grant_excite_activity_award(activity_id, redis_key, award_center_type, timestamp=0):
    ''' 精彩活动结束时 定时发放未领的奖励到领奖中心 
    @param: activity_id-精彩活动ID
    @param: redis_key-精彩活动对应的redis_key
    @param: award_center_type-领奖中心奖励类型
    @param: timestamp-借用时间戳作为callLater的有效性验证
    '''
    log.warn('excite activity award. activity_id: {0}, timestamp: {1}, ACTIVITY_AWARD_TIME: {2}.'.format( activity_id, timestamp, (PAY_ACTIVITY_AWARD_TIME,CONSUME_ACTIVITY_AWARD_TIME) ))

    _field = None
    _award_conf = None
    # 判断是否是正确的callLater
    if activity_id == EXCITE_PAY_ACTIVITY:
        _field = 'TotalPay'
        _award_conf = get_pay_activity_conf()
        if PAY_ACTIVITY_AWARD_TIME != timestamp:
            defer.returnValue( None )
    elif activity_id == EXCITE_CONSUME_ACTIVITY:
        _field = 'TotalConsume'
        _award_conf = get_consume_activity_conf()
        if CONSUME_ACTIVITY_AWARD_TIME != timestamp:
            defer.returnValue( None )

    if not _award_conf:
        defer.returnValue( None )

    _all_data = yield redis.hgetall( redis_key )
    if not _all_data:
        defer.returnValue( None )
    # 进领奖中心 
    for _cid, _data in _all_data.iteritems():
        _data = loads(_data)
        _award_ids = []
        for _award in _award_conf.itervalues():
            if _award['ID'] in _data[0] or _award['ID'] in _award_ids:
                continue
            if _award[_field] <= _data[1]:
                _award_ids.append( _award['ID'] )
                yield g_AwardCenterMgr.new_award( _cid, award_center_type, [int(time()), activity_id, _award['ID']] )
    # 删除旧的活动数据
    yield redis.delete( redis_key )


@defer.inlineCallbacks
def check_excite_activity(activity_id, deleted=False):
    ''' 检查精彩活动中是否有定时活动并定时开启, 活动结束后定时把未领奖励发到领奖中心
    @param: deleted-True:清除旧数据, False:不清除
    '''
    global PAY_ACTIVITY_AWARD_TIME, CONSUME_ACTIVITY_AWARD_TIME, GROUP_BUY_AWARD_TIME

    _redis_key = None
    _award_center_type = AWARD_TYPE_UNKNOWN
    if activity_id == EXCITE_PAY_ACTIVITY:
        _redis_key = HASH_PAY_ACTIVITY
        _award_center_type = AWARD_TYPE_PAY_ACTIVITY
        PAY_ACTIVITY_AWARD_TIME = int(time())
    elif activity_id == EXCITE_CONSUME_ACTIVITY:
        _redis_key = HASH_CONSUME_ACTIVITY
        _award_center_type = AWARD_TYPE_CONSUME_ACTIVITY
        CONSUME_ACTIVITY_AWARD_TIME = int(time())
    elif activity_id == EXCITE_PAY_CREDITS_BACK:
        _redis_key = HASH_PAY_CREDITS_BACK

    elif activity_id == EXCITE_GROUP_BUY:
        _redis_key = DICT_GROUP_BUY_PERSON_INFO
        GROUP_BUY_AWARD_TIME = int(time())
        _award_center_type = AWARD_TYPE_GROUP_BUY

    if not _redis_key:
        defer.returnValue( None )

    _all_excite_conf = get_excite_activity_conf()
    for _excite_conf in _all_excite_conf.itervalues():
        if _excite_conf['ActivityID'] == activity_id:
            break
    else:
        yield redis.delete( _redis_key )
        defer.returnValue( None )

    # 每次OSS同步会删除旧的数据, 策划要求
    if deleted:
        yield redis.delete( _redis_key )

    # 定时发放奖励 针对活动结束时需要发放奖励的活动
    if activity_id == EXCITE_PAY_ACTIVITY:
        interval_seconds = datetime2time( _excite_conf['CloseTime'] )- PAY_ACTIVITY_AWARD_TIME
        log.warn('excite activity would award to award center after {0} seconds, activity_id: {1}.'.format( interval_seconds, activity_id ))
        if interval_seconds <= 0:
            defer.returnValue( None )
        reactor.callLater( interval_seconds, grant_excite_activity_award, activity_id, _redis_key, _award_center_type, PAY_ACTIVITY_AWARD_TIME )
    elif activity_id == EXCITE_CONSUME_ACTIVITY:
        interval_seconds = datetime2time( _excite_conf['CloseTime'] )- CONSUME_ACTIVITY_AWARD_TIME
        log.warn('excite activity would award to award center after {0} seconds, activity_id: {1}.'.format( interval_seconds, activity_id ))
        if interval_seconds <= 0:
            defer.returnValue( None )
        reactor.callLater( interval_seconds, grant_excite_activity_award, activity_id, _redis_key, _award_center_type, CONSUME_ACTIVITY_AWARD_TIME )

    elif activity_id == EXCITE_GROUP_BUY:
        interval_seconds = datetime2time( _excite_conf['CloseTime'] )- GROUP_BUY_AWARD_TIME
        log.warn('excite activity would award to award center after {0} seconds, activity_id: {1}.'.format( interval_seconds, activity_id ))
        if interval_seconds <= 0:
            defer.returnValue( None )
        reactor.callLater( interval_seconds, grant_group_buy_award, activity_id, _redis_key, _award_center_type, GROUP_BUY_AWARD_TIME )
    defer.returnValue( None )

try:
    PAY_ACTIVITY_AWARD_TIME, CONSUME_ACTIVITY_AWARD_TIME, GROUP_BUY_AWARD_TIME
except:
    PAY_ACTIVITY_AWARD_TIME = CONSUME_ACTIVITY_AWARD_TIME = GROUP_BUY_AWARD_TIME = int(time())


