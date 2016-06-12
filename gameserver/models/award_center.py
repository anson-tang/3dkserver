#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time     import time
from log      import log
from marshal  import loads, dumps
from errorno  import *
from constant import *
from redis    import redis
from utils    import split_items, check_valid_time

from protocol_manager       import gw_send, ms_send
from twisted.internet       import defer
from system                 import get_firstpay_reward, get_arena_rank_award, \
        get_climbing_conf, get_monthly_card_conf, get_vip_welfare_conf, get_limit_fellow_award_conf, \
        get_pay_activity_award_conf, get_consume_activity_award_conf, get_daily_quest_reward_conf, \
        get_pay_login_package_conf, get_joust_reward_conf, get_group_buy_reward_list_conf
from models.item            import *
from manager.gsuser         import g_UserMgr


ADD_WAYs = {
             AWARD_TYPE_FIRSTPAY: WAY_FIRSTPAY_AWARD,      #  1:首充奖励
            AWARD_TYPE_ARENARANK: WAY_ARENA_RANK_AWARD,    #  2:竞技场奖励
             AWARD_TYPE_CLIMBING: WAY_CLIMBING_AWARD,      #  3:天外天扫荡奖励
         AWARD_TYPE_MONTGLY_CARD: WAY_MONTHLY_CARD_AWARD,  #  4:未领的月卡奖励
          AWARD_TYPE_VIP_WELFARE: WAY_VIP_WELFARE,         #  5:未领的VIP福利
    AWARD_TYPE_LIMIT_FELLOW_RANK: WAY_LIMIT_FELLOW,        #  6:限时神将排名奖励
   AWARD_TYPE_LIMIT_FELLOW_SCORE: WAY_LIMIT_FELLOW,        #  7:限时神将积分奖励 
         AWARD_TYPE_PAY_ACTIVITY: WAY_PAY_ACTIVITY,        #  8:累计充值奖励
     AWARD_TYPE_CONSUME_ACTIVITY: WAY_CONSUME_ACTIVITY,    #  9:累计消费奖励
            AWARD_TYPE_GIFT_CODE: WAY_GIFT_CODE,           # 10:兑换码礼包奖励
        AWARD_TYPE_CONSTELLATION: WAY_CONSTELLATION_AWARD, # 11:观星未领奖励
          AWARD_TYPE_SCENE_SWEEP: WAY_SCENE_ALL_SWEEP,     # 12:副本全扫荡奖励
                   AWARD_TYPE_GM: WAY_GM_AWARD,            # 13:GM奖励
          AWARD_TYPE_ARENA_LUCKY: WAY_ARENA_LUCK_RANK,     # 14:竞技场幸运排名奖励
          AWARD_TYPE_DAILY_QUEST: WAY_DAILY_QUEST,         # 15:每日任务的未领奖励
       AWARD_TYPE_WORLDBOSS_RANK: WAY_WORLDBOSS_RANK,      # 16:世界Boss排名奖励
            AWARD_TYPE_PAY_LOGIN: WAY_PAY_LOGIN_PACKAGE,   # 17:豪华签到未领的奖励
   AWARD_TYPE_WORLDBOSS_LASTKILL: WAY_WORLDBOSS_KILL,      # 18:世界Boss击杀奖励
            AWARD_TYPE_JOUSTRANK: WAY_JOUST_RANK_AWARD,    # 19:大乱斗排名奖励
     AWARD_TYPE_PAY_CREDITS_BACK: WAY_PAY_CREDITS_BACK,    # 20:充值返利
            AWARD_TYPE_GROUP_BUY: WAY_GROUP_BUY,           # 21:团购奖励
      AWARD_TYPE_RESOURCE_REWARD: WAY_RESOURCE_REWARD,     # 22:第一次下载资源包的奖励
        }

def get_award_conf(award_type, *args):
    '''
    @summary: 1.检查是否过期 2.返回items_list
    @param  : award_type-奖励类型。
    @param  : args-默认奖励类型的参数格式为[timestamp, items_list]
    '''
    items_list = []
    if not args:
        return AWARD_TIME_EXPIRE, []
    # 检查时间是否过期, 14天改为3天
    if check_valid_time(args[0], hour=AWARD_VALID_HOURS):
        return AWARD_TIME_EXPIRE, []

    if award_type == AWARD_TYPE_FIRSTPAY:
        reward_conf = get_firstpay_reward()
        if reward_conf:
            items_list = [[_r['ItemType'], _r['ItemID'], _r['ItemNum']] for _r in reward_conf]
    elif award_type == AWARD_TYPE_ARENARANK:
        #award_time, _rank = args
        arena_rank_conf = get_arena_rank_award( args[1] )
        if arena_rank_conf:
            items_list = split_items( arena_rank_conf['ArenaRankList'] )
    elif award_type == AWARD_TYPE_CLIMBING:
        for _layer in args[1]:
            climbing_conf = get_climbing_conf( _layer )
            if climbing_conf:
                items_list = add_new_items([1, 1, climbing_conf['RewardGold']], items_list)
                items_list = add_new_items([1, 4, climbing_conf['RewardSoul']], items_list)
                for _v in climbing_conf['BonusList']:
                    items_list = add_new_items(_v, items_list)
    elif award_type == AWARD_TYPE_MONTGLY_CARD:
        back_credits = get_monthly_card_conf(MONTHLY_CARD_NORMAL)
        if back_credits:
            items_list = [[ITEM_TYPE_MONEY, ITEM_MONEY_CREDITS, back_credits]]
    elif award_type == AWARD_TYPE_VIP_WELFARE:
        pass
        #welfare_conf = get_vip_welfare_conf()
        #items_list   = welfare_conf.get(args[1], [])
    elif award_type in [AWARD_TYPE_LIMIT_FELLOW_RANK, AWARD_TYPE_LIMIT_FELLOW_SCORE]:
        limit_fellow_conf = get_limit_fellow_award_conf(args[1])
        items_list   = limit_fellow_conf.get(args[2], {}).get('AwardList', [])
    elif award_type == AWARD_TYPE_PAY_ACTIVITY:
        _award_conf = get_pay_activity_award_conf( args[2] )
        items_list  = _award_conf.get('AwardList', [])
    elif award_type == AWARD_TYPE_CONSUME_ACTIVITY:
        _award_conf = get_consume_activity_award_conf( args[2] )
        items_list  = _award_conf.get('AwardList', [])
    elif award_type == AWARD_TYPE_SCENE_SWEEP:
        items_list  = args[2]
    elif award_type == AWARD_TYPE_DAILY_QUEST:
        for reward_id in args[1]:
            _reward_conf = get_daily_quest_reward_conf(reward_id)
            if not _reward_conf:
                continue
            for _v in _reward_conf['Reward']:
                items_list = add_new_items(_v, items_list)
    elif award_type == AWARD_TYPE_PAY_LOGIN:
        _award_conf = get_pay_login_package_conf( args[1] )
        items_list  = _award_conf.get('RewardList', [])
    elif award_type == AWARD_TYPE_JOUSTRANK:
        items_list  = get_joust_reward_conf( args[1] )
    elif award_type == AWARD_TYPE_GROUP_BUY:
        items_list = []
        for buy_type, buy_count in args[2]:
            _reward = get_group_buy_reward_list_conf(buy_type, buy_count)      
            _item_type, _item_id, _item_num = _reward.split(":")
            items_list.append([int(_item_type), int(_item_id), int(_item_num)])
    elif award_type == AWARD_TYPE_RESOURCE_REWARD:
        items_list = [[ITEM_TYPE_PACKAGE, RESOURCE_PACKAGE_ID, 1]]
    else:
        items_list  = args[1]

    return NO_ERROR, items_list

class AwardCenterMgr(object):
    '''
    @summary: 领奖中心
    @param  : award_type 奖励类型。1:首充奖励; 2:竞技场奖励; 3:天外天扫荡奖励; 4:月卡奖励; 
          5:VIP福利; 6:限时神将排名奖励; 7:限时神将积分奖励; 8:累计充值奖励; 9:累计消费奖励; 
          10:兑换码礼包奖励; 11:观星未领奖励; 12:副本全扫荡奖励; 13:GM奖励; 14:竞技场幸运排名奖励; 
          15:每日任务的未领奖励; 16:世界Boss排名奖励; 17:豪华签到未领的奖励; 18:世界Boss击杀奖励;
          19:大乱斗排名奖励; 20:充值返利; 21:团购奖励
    '''
    @defer.inlineCallbacks
    def award_center_info(self, cid):
        '''
        @summary: 获取玩家的奖励信息
        @param  : 详见redis_data_record.py说明
        '''
        _award_info  = [] # 玩家的奖励列表
        _expired_ids = [] # 过期的award_ids
        _all_data = yield redis.hgetall( HASH_AWARD_CENTER%cid )
        if _all_data:
            for _data in _all_data.itervalues():
                _data = loads( _data )
                if len(_data) != 3:
                    continue
                res_err, items_list = get_award_conf(_data[1], *_data[2])
                if res_err:
                    _expired_ids.append( _data[0] )
                    continue
                if not items_list:
                    log.error('No conf in award center. cid: {0}, _data: {1}.'.format( cid, _data ))
                    continue
                ## 过滤掉天外天中的塔层
                #if _data[1] == AWARD_TYPE_CLIMBING:
                #    _award_info.append( [_data[0], _data[1], [_data[2][0], items_list]] )
                ## 过滤掉VIP福利的VIP Level
                #elif _data[1] == AWARD_TYPE_VIP_WELFARE:
                #    _award_info.append( [_data[0], _data[1], [_data[2][0], items_list]] )
                ## 过滤掉限时神将的活动ID、排名
                #elif _data[1] in [AWARD_TYPE_LIMIT_FELLOW_RANK, AWARD_TYPE_LIMIT_FELLOW_SCORE]:
                #    _award_info.append( [_data[0], _data[1], [_data[2][0], items_list]] )
                ## 过滤掉累计充值、累计消费的活动ID、奖励ID列表
                #elif _data[1] in [AWARD_TYPE_PAY_ACTIVITY, AWARD_TYPE_CONSUME_ACTIVITY]:
                #    _award_info.append( [_data[0], _data[1], [_data[2][0], items_list]] )
                ## 过滤掉每日任务中的奖励档次ID
                #elif _data[1] == AWARD_TYPE_DAILY_QUEST:
                #    _award_info.append( [_data[0], _data[1], [_data[2][0], items_list]] )

                # 组织奖励信息
                if _data[1] in [AWARD_TYPE_CLIMBING, AWARD_TYPE_VIP_WELFARE, AWARD_TYPE_LIMIT_FELLOW_RANK, \
                        AWARD_TYPE_LIMIT_FELLOW_SCORE, AWARD_TYPE_PAY_ACTIVITY, AWARD_TYPE_CONSUME_ACTIVITY, \
                        AWARD_TYPE_DAILY_QUEST, AWARD_TYPE_PAY_LOGIN, AWARD_TYPE_JOUSTRANK, AWARD_TYPE_GROUP_BUY]:
                    _award_info.append( [_data[0], _data[1], [_data[2][0], items_list]] )
                elif _data[1] in [AWARD_TYPE_FIRSTPAY, AWARD_TYPE_ARENARANK, AWARD_TYPE_MONTGLY_CARD, AWARD_TYPE_RESOURCE_REWARD]:
                    _data[2].append( items_list )
                    _award_info.append( _data )
                else: # 不需要任何处理
                    _award_info.append( _data )

        if _expired_ids:
            yield redis.hdel( HASH_AWARD_CENTER % cid, *_expired_ids )
            #log.info('For Test. Del Redis Data. _expired_ids: {0}.'.format( _expired_ids ))

        defer.returnValue( _award_info )

    @defer.inlineCallbacks
    def get_award_center(self, user, get_award_type, award_id):
        '''
        @summary: 领奖
        @param  : get_award_type 1:单次领奖; 2:全部领取;
                  award_id : get_award_type为2时, 此字段无意义
        '''
        items_return = [] # 返回背包的道具信息
        awarded_ids  = [] # 已领奖的award_ids
        if get_award_type == 1: # 单次领奖
            _data = yield redis.hget( HASH_AWARD_CENTER % user.cid, award_id )
            if not _data:
                log.error('Can not find the award. cid:{0}.'.format( user.cid ))
                defer.returnValue( REQUEST_LIMIT_ERROR )
            _data = loads( _data )
            if len(_data) != 3:
                log.error('redis data error. cid:{0}, _data:{1}.'.format( user.cid, _data ))
                defer.returnValue( UNKNOWN_ERROR )
            awarded_ids.append( _data[0] )
            items_return = yield self.get_one_award( user, _data, items_return )

        elif get_award_type == 2: # 全部领取
            _all_data = yield redis.hgetall( HASH_AWARD_CENTER % user.cid )
            if not _all_data:
                log.error('Can not find the award. cid:{0}.'.format( user.cid ))
                defer.returnValue( REQUEST_LIMIT_ERROR )
            for _data in _all_data.itervalues():
                _data = loads( _data )
                if len(_data) != 3:
                    log.error('redis data error. cid:{0}, _data: {1}.'.format( user.cid, _data ))
                    continue
                awarded_ids.append( _data[0] )
                items_return = yield self.get_one_award( user, _data, items_return )

        if awarded_ids:
            yield redis.hdel( HASH_AWARD_CENTER % user.cid, *awarded_ids )
            #log.info('For Test. get_award_center. Del Redis Data. awarded_ids: {0}.'.format( awarded_ids ))
 
        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def get_one_award(self, user, data, items_return):
        '''
        @summary: 往玩家背包中添加道具
        @param  : items-返回给client的数据
        '''
        res_err, items_list = get_award_conf(data[1], *data[2])
        if res_err:
            defer.returnValue( items_return )

        add_type = ADD_WAYs.get(data[1], WAY_UNKNOWN)
        # 道具进背包
        for _type, _id, _num in items_list:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. cid:{0}, item info: {1}.'.format( user.cid, (_type, _id, _num) ))
                continue
            res_err, value = yield model(user, ItemID=_id, ItemNum=_num, AddType=add_type, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    items_return = total_new_items( _v, items_return )
        # 发邮件
        if AWARD_TYPE_JOUSTRANK == data[1] and items_list:
            ms_send('write_mail', (user.cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_2, [data[2][1], items_list], data[2][0]))
        elif AWARD_TYPE_ARENARANK == data[1] and items_list:
            ms_send('write_mail', (user.cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_1, [data[2][0], data[2][1], items_list], data[2][0]))
        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def new_award(self, cid, award_type, args, flag=True):
        '''
        @summary: 新增奖励
        @param  : args由award_type确定
            award_type=1,4,22 args = [timestamp]
            award_type=2, args = [timestamp, rank]
            award_type=3, args = [timestamp, [tower_layer, ...]]
            award_type=5, args = [timestamp, vip_level]
            award_type=6, 7, args = [timestamp, activity_id, rank]
            award_type=8, 9, args = [timestamp, activity_id, award_id]
            award_type=10,11,13,14,16,20 args = [timestamp, [[item_type, item_id, item_num], ...]]
            award_type=12 args = [timestamp, scene_id, [[item_type, item_id, item_num], ...]]
            award_type=15, args = [timestamp, [reward_id, ...]]
            award_type=17, args = [timestamp, package_id]
            award_type=19, args = [timestamp, joust_rank]
            award_type=21, args = [timestamp, activity_id, Array([buy_type, buy_count],..)]
        @param  : flag是否通知client的标志位
        '''
        add_type = ADD_WAYs.get(award_type, None)
        if not add_type: # 未知奖励类型
            defer.returnValue( UNKNOWN_ERROR )

        if award_type in [AWARD_TYPE_FIRSTPAY, AWARD_TYPE_MONTGLY_CARD, AWARD_TYPE_RESOURCE_REWARD]:
            if len(args) != 1:
                defer.returnValue( CLIENT_DATA_ERROR )
        elif award_type in [AWARD_TYPE_LIMIT_FELLOW_RANK, AWARD_TYPE_LIMIT_FELLOW_SCORE, \
                AWARD_TYPE_PAY_ACTIVITY, AWARD_TYPE_CONSUME_ACTIVITY, AWARD_TYPE_SCENE_SWEEP, AWARD_TYPE_GROUP_BUY]:
            if len(args) != 3:
                defer.returnValue( CLIENT_DATA_ERROR )
        else:
            if len(args) != 2:
                defer.returnValue( CLIENT_DATA_ERROR )
        # 新增奖励记录
        _primary = yield redis.hincrby( HASH_HINCRBY_KEY, AWARD_ID, 1 )
        _data    = [_primary, award_type, args]
        yield redis.hset( HASH_AWARD_CENTER % cid, _primary, dumps(_data) )
        # 只通知当时在线的玩家
        if flag and g_UserMgr.online_status(cid):
            gw_send( cid, 'sync_multicast', [SYNC_MULTICATE_TYPE_1, []] )

        defer.returnValue( NO_ERROR )

g_AwardCenterMgr = AwardCenterMgr()
