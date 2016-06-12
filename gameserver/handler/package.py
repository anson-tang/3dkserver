#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from rpc        import route
from log        import log
from time       import time
from datetime   import datetime, timedelta
from errorno    import *
from constant   import *
from redis      import redis
from marshal    import loads, dumps
from utils      import datetime2time
from syslogger        import syslogger

from twisted.internet    import defer
from manager.gsuser      import g_UserMgr
from system              import get_max_login_package_id, get_login_package_conf, \
        get_level_package_conf, get_all_openservice_id, get_openservice_package_conf, \
        get_online_package_conf, get_all_online_group, get_all_online_package_id, \
        get_max_pay_login_package_id, get_pay_login_package_conf
from models.item         import *

from models.daily_pay    import get_daily_pay_record
from models.award_center import g_AwardCenterMgr


@route()
@defer.inlineCallbacks
def package_status(p, req):
    '''
    @return: 依次为开服礼包、签到礼包、等级礼包、在线礼包的状态
    '''
    res_err = UNKNOWN_ERROR
    
    cid, = req
    
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    _status_1 = yield get_openservice_status(cid)
    # 获取最大的package_id
    _max_package_id = get_max_login_package_id()
    _status_2 = yield get_login_status(cid, HASH_LOGIN_PACKAGE, _max_package_id)
    _status_3 = yield get_level_status(cid)
    _status_4 = yield get_online_status(cid)

    defer.returnValue( [_status_1[1:], _status_2, _status_3, _status_4] )

@route()
@defer.inlineCallbacks
def login_package_reward(p, req):
    '''
    @return: add_items
    '''
    res_err = UNKNOWN_ERROR
    
    cid, = req
 
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    # 获取最大的package_id
    _max_package_id = get_max_login_package_id()
    _, package_id = yield get_login_status(cid, HASH_LOGIN_PACKAGE, _max_package_id)
    if package_id == 0:
        log.error('No login reward. cid: {0}.'.format( cid ))
        defer.returnValue( REQUEST_LIMIT_ERROR )

    conf = get_login_package_conf( package_id )
    if not conf:
        log.error('No login package conf. cid: {0}, package_id: {1}.'.format( cid, package_id ))
        defer.returnValue( NOT_FOUND_CONF )

    items_return = []
    yield redis.hset(HASH_LOGIN_PACKAGE, user.cid, dumps([int(time()), package_id]))
    for _type, _id, _num in conf['RewardList']:
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. cid: {0}, item: {1}.'.format( cid, (_type, _id, _num) ))
            continue
        res_err, value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_LOGIN_PACKAGE, CapacityFlag=False)
        if not res_err and value:
            for _v in value:
                items_return = total_new_items( _v, items_return )

    # 每日任务计数
    yield user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_11, 1 )

    defer.returnValue( items_return )

@route()
@defer.inlineCallbacks
def online_package_reward(p, req):
    '''
    @return: (group, package_id, next_reward_timestamp, add_items)
    '''
    res_err = UNKNOWN_ERROR
    
    cid, = req
 
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    package_group, package_id, next_reward_timestamp = yield get_online_status(user.cid)

    if not package_group or not package_id:
        log.error('No online reward. cid: {0}.'.format( cid ))
        defer.returnValue( REQUEST_LIMIT_ERROR )
    # 倒计时未结束
    if next_reward_timestamp > int(time()):
        log.error('Get online reward time limit. cid: {0}, left_timesamp: {1}.'.format( cid, next_reward_timestamp-int(time()) ))
        defer.returnValue( REQUEST_LIMIT_ERROR )
    # 0-今天的奖励已领完, 明天的第一个奖励标志位
    if package_id == 1 and next_reward_timestamp == 0:
        log.warn('All online reward have been gotten today. cid: {0}.'.format( cid ))
        defer.returnValue( NO_PACKAGE_REWARD )

    # conf
    conf = get_online_package_conf(package_group, package_id)
    if not conf:
        log.error('Unknown online package. cid: {0}, package_group: {1}, package_id: {2}.'.format( cid, package_group, package_id ))
        defer.returnValue( NOT_FOUND_CONF )
    # redis data
    _data = yield redis.hget(HASH_ONLINE_PACKAGE, cid )
    if _data:
        _data = loads(_data)
    else:
        log.error('Unknown error.')
        defer.returnValue( REQUEST_LIMIT_ERROR )
    # 获取最大的package_id
    _all_group = get_all_online_group()
    _max_group = max(_all_group) if _all_group else 0
    _all_ids   = get_all_online_package_id( package_group )
    _max_id    = max(_all_ids) if _all_ids else 0
    # 判断是不是group的最后一个package_id
    next_package_id    = 0
    next_package_group = 0
    next_reward_timestamp = 0
    if package_id >= _max_id:
        next_package_id = 1
        if package_group >= _max_group:
            next_package_group = _max_group
        else:
            next_package_group = package_group + 1
        # 有可领取的礼包组奖励
        if _data[4] > 0:
            _data[4] -= 1
            next_conf = get_online_package_conf(next_package_group, next_package_id)
            if next_conf:
                next_reward_timestamp = int(time() + next_conf['OnlineTime'])
            yield redis.hset( HASH_ONLINE_PACKAGE, cid, dumps( [next_package_group, next_package_id, next_reward_timestamp, _data[3], _data[4]] ) )
        else: # 已领完当天的奖励
            yield redis.hset( HASH_ONLINE_PACKAGE, cid, dumps( [next_package_group, next_package_id, next_reward_timestamp, _data[3], _data[4]] ) )
    else:
        next_package_id    = package_id + 1
        next_package_group = package_group
        next_conf = get_online_package_conf(next_package_group, next_package_id)
        if next_conf:
            next_reward_timestamp = int(time() + next_conf['OnlineTime'])
        yield redis.hset( HASH_ONLINE_PACKAGE, cid, dumps( [next_package_group, next_package_id, next_reward_timestamp, _data[3], _data[4]] ) )

    items_return = []
    for _type, _id, _num in conf['RewardList']:
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. cid: {0}, item: {1}.'.format( cid, (_type, _id, _num) ))
            continue
        res_err, value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_ONLINE_PACKAGE, CapacityFlag=False)
        if not res_err and value:
            for _v in value:
                items_return = total_new_items( _v, items_return )

    defer.returnValue( (next_package_group, next_package_id, next_reward_timestamp, items_return) )


@route()
@defer.inlineCallbacks
def level_package_reward(p, req):
    '''
    @summary: 领取等级礼包奖励
    '''
    res_err = UNKNOWN_ERROR
    
    cid, [level]= req
 
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    conf = get_level_package_conf(level)
    if not conf:
        log.error('Unknown level package. cid: {0}, level: {1}.'.format( cid, level ))
        defer.returnValue( NOT_FOUND_CONF )
    # 玩家等级不满足 
    if level > user.base_att.level:
        log.error('User level limit. cid: {0}, need: {1}, cur: {2}.'.format( cid, level, user.base_att.level ))
        defer.returnValue( REQUEST_LIMIT_ERROR )

    old_level = yield get_level_status(cid)
    if level in old_level:
        log.error('Had got the reward. cid: {0}, level: {1}.'.format( cid, level ))
        defer.returnValue( REPEAT_REWARD_ERROR )
    # 保存已领取的玩家等级礼包记录
    old_level.append( level )
    yield redis.hset(HASH_LEVEL_PACKAGE, cid, dumps(old_level))
    # 等级礼包道具进玩家背包
    items_return = []
    for _type, _id, _num in conf['RewardList']:
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. cid: {0}, item: {1}.'.format( cid, (_type, _id, _num) ))
            continue
        res_err, value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_LEVELUP_PACKAGE, CapacityFlag=False)
        if not res_err and value:
            for _v in value:
                items_return = total_new_items( _v, items_return )

    defer.returnValue( items_return )

@route()
@defer.inlineCallbacks
def openservice_package_reward(p, req):
    '''
    @summary: 礼包按照ID顺序领取, 全部领取后Icon消失。
    '''
    res_err = UNKNOWN_ERROR
    
    cid, [package_id]= req
 
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    conf = get_openservice_package_conf( package_id )
    if not conf:
        log.error('No openservice package conf. cid: {0}, package_id: {1}.'.format( user.cid, package_id ))
        defer.returnValue( NOT_FOUND_CONF )
 
    login_timestamp, got_package_ids, max_can_get_id = yield get_openservice_status(cid)
    if package_id in got_package_ids:
        log.error('Had got the reward. cid: {0}, package_id: {1}.'.format( cid, package_id ))
        defer.returnValue( REPEAT_REWARD_ERROR )
    if package_id > max_can_get_id:
        log.error('Can not get the reward. cid: {0}, package_id: {1}, max_can_get_id: {2}.'.format( cid, package_id, max_can_get_id ))
        defer.returnValue( REQUEST_LIMIT_ERROR )
    # 保存已领取的玩家开服礼包记录
    got_package_ids.append( package_id )

    items_return = []
    yield redis.hset(HASH_OPENSERVICE_PACKAGE, user.cid, dumps([login_timestamp, got_package_ids, max_can_get_id]))
    syslogger(LOG_OPEN_SERVICE_PACKAGE, cid, user.level, user.vip_level, user.alliance_id, package_id)
    for _type, _id, _num in conf['RewardList']:
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. cid: {0}, item: {1}.'.format( user.cid, (_type, _id, _num) ))
            continue
        res_err, value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_OPENSERVICE_PACKAGE, CapacityFlag=False)
        if not res_err and value:
            for _v in value:
                items_return = total_new_items( _v, items_return )

    defer.returnValue( items_return )

@defer.inlineCallbacks
def get_login_status(cid, redis_key, max_package_id):
    '''
    @summary: 连续登录天数，连续登录中断后从1开始记，连续登录天数超过配置条数则领取最后一条奖励
    '''
    _data = yield redis.hget(redis_key, cid)
    if _data:
        _data = loads(_data)
    else:
        _data = [0, 0]
    # 判断时间点
    _d_time  = datetime.fromtimestamp( _data[0] )
    _d_now   = datetime.now()
    _delta   = _d_now - _d_time
    if _delta.days < 2:
        # 同一天重复登录
        if _d_now.day == _d_time.day:
            defer.returnValue( (_data[1], 0) )
        # 连续登录
        elif (_d_now.day - _d_time.day == 1):
            if _data[1] >= max_package_id:
                defer.returnValue( (_data[1], max_package_id) )
            else:
                defer.returnValue( (_data[1], _data[1] + 1) )
    # 非连续登录
    defer.returnValue( (0, 1) )

@defer.inlineCallbacks
def get_online_status(cid):
    '''
    @summary: 在线礼包的状态
    '''
    _data = yield redis.hget(HASH_ONLINE_PACKAGE, cid )
    if _data:
        _data = loads(_data)
    else:
        _data = [0, 0, 0, 0, 0]
    if not _data[0]:
        conf = get_online_package_conf(1, 1)
        if not conf:
            log.error('Can not find conf. cid: {0}.'.format( cid ))
            defer.returnValue( [0, 0, 0] )
        _data = [1, 1, int(time()+conf['OnlineTime']), int(time()), 0]
        yield redis.hset(HASH_ONLINE_PACKAGE, cid, dumps( _data ))
        defer.returnValue( [_data[0], _data[1], _data[2]] )
    # 计算离线时间
    _d_time  = datetime.fromtimestamp( _data[3] )
    _d_now   = datetime.now()
    _delta   = _d_now - _d_time
    # 同一天的礼包已领完
    if _delta.days < 1 and _d_now.day == _d_time.day:
        if _data[4] <= 0:
            log.debug('The last group online. cid: {0}.'.format( cid ))
            defer.returnValue( [_data[0], _data[1], _data[2]] )
    else:
        _data[4] = 0 # 每天在线可领一个group
        if _data[1] > 1: # 上一组没有领完可继续领取并可领取下一个组
            _data[4] = 1
        # next_reward_timestamp=0时, 表示领取今天的第一个奖励
        if not _data[2]:
            conf = get_online_package_conf(_data[0], _data[1])
            if conf:
                _data[2] = int(time() + conf['OnlineTime'])
        _data[3] = int(time())
        yield redis.hset( HASH_ONLINE_PACKAGE, cid, dumps(_data) )

    defer.returnValue( [_data[0], _data[1], _data[2]] )

@defer.inlineCallbacks
def get_level_status(cid):
    '''
    @summary: 礼包全部领取后ICON消失
    '''
    _data = yield redis.hget(HASH_LEVEL_PACKAGE, cid)
    if _data:
        _data = loads(_data)
    else:
        _data = []

    defer.returnValue( _data )

@defer.inlineCallbacks
def get_openservice_status(cid):
    '''
    @summary: 开服礼包只要玩家登录即可无序领取
    '''
    _data = yield redis.hget(HASH_OPENSERVICE_PACKAGE, cid)
    _data = loads(_data) if _data else [0, [], 0]
    # 获取最大的package_id
    _all_ids = get_all_openservice_id()
    _max_id  = max(_all_ids) if _all_ids else 0
    if _data[2] > _max_id:
        defer.returnValue( (_data[0], _data[1], _max_id) )
    # 判断时间点
    _d_time  = datetime.fromtimestamp( _data[0] )
    _d_now   = datetime.now()
    _delta   = _d_now - _d_time
    # 同一天重复登录
    if _d_now.day == _d_time.day and _delta.days < 1:
        defer.returnValue( (_data[0], _data[1], _data[2]) )
    
    _data[0] = int(time())
    yield redis.hset(HASH_OPENSERVICE_PACKAGE, cid, dumps([_data[0], _data[1], _data[2]+1]))
    defer.returnValue( (_data[0], _data[1], _data[2]+1) )

@route()
@defer.inlineCallbacks
def set_openservice_info(p, req):
    ''' used for test '''
    cid, [package_id] = req

    #user = g_UserMgr.getUser(cid)
    #if not user:
    #    log.error('Can not find user. cid: {0}.'.format( cid ))
    #    defer.returnValue( CONNECTION_LOSE )

    yield redis.hset(HASH_OPENSERVICE_PACKAGE, cid, dumps([0, [], package_id]))
    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def pay_login_package_status(p, req):
    '''
    @summary: 豪华签到礼包, 连续登录天数，连续登录中断后从1开始记，连续登录天数超过配置条数则领取最后一条奖励
    '''
    cid, = req
 
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )
    # had total cost
    _had_cost = yield get_daily_pay_record(cid)

    # 获取最大的package_id
    _max_package_id = get_max_pay_login_package_id()
    _status = yield get_pay_login_status(cid, HASH_PAY_LOGIN_PACKAGE, _max_package_id)

    defer.returnValue( (_status[0], _status[1], _had_cost) )

@route()
@defer.inlineCallbacks
def pay_login_package_reward(p, req):
    ''' get pay_login_package reward.
    '''
    cid, = req
 
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 获取最大的package_id
    _max_package_id = get_max_pay_login_package_id()
    _, package_id = yield get_pay_login_status(cid, HASH_PAY_LOGIN_PACKAGE, _max_package_id)
    if package_id == 0:
        log.error('No pay login reward can be got. cid: {0}.'.format( cid ))
        defer.returnValue( PAY_LOGIN_REWARD_HAD_GOT )

    conf = get_pay_login_package_conf( package_id )
    if not conf:
        log.error('No pay login package conf. cid: {0}, package_id: {1}.'.format( cid, package_id ))
        defer.returnValue( NOT_FOUND_CONF )

    # had total cost
    _had_cost = yield get_daily_pay_record(cid)
    if conf['NeedCost'] > _had_cost:
        log.error('Daily pay not enough. cid: {0}, package_id: {1}, need cost: {2}, had cost: {3}.'.format( cid, package_id, conf['NeedCost'], _had_cost ))
        defer.returnValue(PAY_LOGIN_COST_NOT_ENOUGH)

    items_return = []
    yield redis.hset(HASH_PAY_LOGIN_PACKAGE, user.cid, dumps([int(time()), package_id, 1]))
    for _type, _id, _num in conf['RewardList']:
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. cid: {0}, item: {1}.'.format( cid, (_type, _id, _num) ))
            continue
        res_err, value = yield model(user, ItemID=_id, ItemNum=_num, AddType=WAY_LOGIN_PACKAGE, CapacityFlag=False)
        if not res_err and value:
            for _v in value:
                items_return = total_new_items( _v, items_return )

    defer.returnValue( items_return )

@defer.inlineCallbacks
def get_pay_login_status(cid, redis_key, max_package_id):
    '''
    @summary: 连续登录天数，连续登录中断后从1开始记，连续登录天数超过配置条数则领取最后一条奖励
    '''
    _data = yield redis.hget(redis_key, cid)
    if _data:
        _data = loads(_data)
    else:
        _data = [0, 1, 0]
    # 第一次充值签到
    if not _data[0]:
        defer.returnValue( (0, 1) )

    # 判断时间点
    _d_now  = datetime.now()
    _d_time = datetime.fromtimestamp( _data[0] )
    _delta  = (_d_now.date() - _d_time.date())

    if _delta.days == 0: # 同一天重复登录
        if _data[2]: # 已签到
            _status = (_data[1], 0)
        else: # 未签到
            _status = ( 0 if _data[1] < 1 else _data[1] -1, _data[1])
        defer.returnValue( _status )

    # 判断是否满足签到条件
    if not _data[2]:
        res_err = yield reward_to_center(cid, _d_time, _data[1])
        if res_err or _delta.days > 1:
            yield redis.hdel(redis_key, cid)
        else:
            _data[2] = 1

    if _data[2] and _delta.days == 1: # 前一天已签到, 连续登录
        if _data[1] >= max_package_id:
            _next_package_id = max_package_id
        else:
            _next_package_id = _data[1] + 1
        _status = (_data[1], _next_package_id)
        yield redis.hset(redis_key, cid, dumps([int(time()), _next_package_id, 0]))
    else:
        _status = (0, 1)

    defer.returnValue( _status )

@defer.inlineCallbacks
def reward_to_center(cid, pay_date, package_id):
    ''' 将未领的豪华签到奖励发放到领奖中心 
    @param: pay_date-查询当天的充值记录
    @param: package_id-豪华签到的礼包ID
    '''
    conf = get_pay_login_package_conf( package_id )
    if not conf:
        defer.returnValue( NOT_FOUND_CONF )

    # had total cost
    _date = pay_date.strftime("%Y-%m-%d")
    _had_cost = yield get_daily_pay_record(cid, _date)

    if conf['NeedCost'] > _had_cost:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    # timestamp-豪华签到奖励的时间点
    timestamp = datetime2time( pay_date )
    yield g_AwardCenterMgr.new_award( cid, AWARD_TYPE_PAY_LOGIN, [timestamp, package_id] )
    # 更新豪华签到记录
    yield redis.hset(HASH_PAY_LOGIN_PACKAGE, cid, dumps([timestamp, package_id, 1]))

    defer.returnValue( NO_ERROR )



