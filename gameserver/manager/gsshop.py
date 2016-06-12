#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from time     import time
from datetime import datetime
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     
from utils    import split_items, get_reset_timestamp, rand_num, timestamp_is_today
from syslogger import syslogger

from twisted.internet       import defer
from system                 import get_item_shop_conf, get_randcard_consume_conf, \
        get_cardpool_shrine_levels, get_cardpool_start_levels, get_randcard_level_count, \
        get_fellow_by_fid, get_randcard_max_level, get_cardpool_conf, get_vip_package, \
        get_campcard_cost_conf, get_campcard_pool_conf
from models.item            import *
from protocol_manager       import gw_broadcast


class GSRandCardMgr(object):
    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

    @defer.inlineCallbacks
    def status(self, camp_flag=False):
        '''
        @summary: 获取抽卡的状态
        @camp_flag: 含阵营抽卡信息的标志位 True-需要返还阵营抽卡的信息 False-不需要
        @param: first_blue-第一次使用钻石抽卡的标志, 0-已使用, 1-未使用
        '''
        blue_data = yield redis.hget(HASH_SHRINE_TYPE % CARD_SHRINE_BLUE, self.cid)
        if blue_data:
            blue_data = loads( blue_data )
            if len(blue_data) == 4:
                _, blue_count, blue_last_free_time, _ = blue_data
                first_blue = 0
            else:
                _, blue_count, blue_last_free_time, _, first_blue, _ = blue_data
        else:
            blue_count, blue_last_free_time, first_blue = 0, 0, 1
        blue_conf = get_randcard_consume_conf( CARD_SHRINE_BLUE )
        blue_need_time = 0
        if blue_conf:
            blue_need_time = self.left_free_timestamp( blue_last_free_time, blue_conf['FreeTime'] )
        # 紫卡的状态
        purple_data = yield redis.hget(HASH_SHRINE_TYPE % CARD_SHRINE_PURPLE, self.cid)
        if purple_data:
            purple_data = loads( purple_data )
            if len(purple_data) == 4:
                purple_level, purple_count, purple_last_free_time, _ = purple_data
                first_purple = 0
            else:
                purple_level, purple_count, purple_last_free_time, _, _, first_purple = purple_data
        else:
            purple_level, purple_count, purple_last_free_time, first_purple = 0, 0, 0, 1
        purple_conf = get_randcard_consume_conf( CARD_SHRINE_PURPLE )
        purple_need_time = 0
        purple_ten_cost  = 0
        if purple_conf:
            purple_need_time = self.left_free_timestamp( purple_last_free_time, purple_conf['FreeTime'] )
            purple_ten_cost  = int((purple_conf['ItemNum'] * 10 * RANDCARD_TEN_RATIO + 99) / 100)
        if purple_need_time >= 0:
            left_purple_count = self.left_purple_count( CARD_SHRINE_PURPLE, purple_level, purple_count )
        else: # 首抽必得
            left_purple_count = 0
        total_num, _ = yield self.user.bag_item_mgr.get_items( ITEM_RANDCARD_GREEN )
        # 阵营抽卡的状态信息
        if camp_flag:
            camp_left_time, curr_camp_data, next_camp_data = yield self.get_campcard_data()
            defer.returnValue( (blue_need_time, purple_need_time, left_purple_count, total_num, purple_ten_cost, first_blue, first_purple, camp_left_time, curr_camp_data, next_camp_data) )
        else:
            defer.returnValue( (blue_need_time, purple_need_time, left_purple_count, total_num, purple_ten_cost, first_blue, first_purple) )

    @defer.inlineCallbacks
    def get_campcard_data(self):
        ''' 获取玩家的阵营抽卡信息 '''
        reset_flag = False
        curr_time  = int(time())
        comm_data  = yield redis.hget(HASH_CAMPRAND_COMMON, 'CAMPRAND')
        if comm_data:
            comm_data = loads(comm_data)
            if curr_time >= comm_data[0]:
                reset_flag = True
                comm_data[0] += CAMP_RAND_TIME
                comm_data[1] = 0 if len(CAMP_GROUP_IDS) <= comm_data[1]+1 else comm_data[1] + 1
                yield redis.hset(HASH_CAMPRAND_COMMON, 'CAMPRAND', dumps(comm_data))
            else:
                camp_data = yield redis.hget(HASH_CAMPRAND_COMMON, self.cid)
                if camp_data:
                    camp_data = loads(camp_data)
                    if 1 == timestamp_is_today(camp_data[0]):
                        curr_camp_data, next_camp_data = camp_data[1], camp_data[2]
                    else:
                        reset_flag = True
                else:
                    reset_flag = True
        else:
            reset_flag = True
            comm_data = [get_reset_timestamp() + CAMP_RAND_TIME, 0]
            yield redis.hset(HASH_CAMPRAND_COMMON, 'CAMPRAND', dumps(comm_data))

        if reset_flag:
            curr_camp_data = [[camp_id, 0] for camp_id in CAMP_GROUP_IDS[comm_data[1]]]
            next_group_id  = 0 if len(CAMP_GROUP_IDS) <= comm_data[1]+1 else comm_data[1] + 1
            next_camp_data = [[camp_id, 0] for camp_id in CAMP_GROUP_IDS[next_group_id]]
            yield redis.hset(HASH_CAMPRAND_COMMON, self.cid, dumps([curr_time, curr_camp_data, next_camp_data]))

        defer.returnValue( (comm_data[0], curr_camp_data, next_camp_data) )

    @defer.inlineCallbacks
    def camp_randcard(self, camp_id):
        ''' 阵营抽卡 '''
        _, curr_camp_data, next_camp_data = yield self.get_campcard_data()
        # 检查阵营, 累计次数
        rand_time = 0
        for _idx, _data in enumerate(curr_camp_data):
            if _data[0] == camp_id:
                if _data[1] >= CAMP_RAND_MAX:
                    defer.returnValue( CAMP_RANDCARD_MAX_LIMIT )
                _data[1] += 1
                rand_time = _data[1]
                curr_camp_data[_idx] = _data
                break
        else:
            defer.returnValue( CAMP_RANDCARD_ID_ERROR )
        # 随机伙伴
        need_credits = get_campcard_cost_conf(rand_time)
        if not need_credits or need_credits > self.user.credits:
            log.error('Credits not enough. cid:{0}, need:{1}, curr: {2}.'.format( self.cid, need_credits, self.user.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )

        pool_conf = get_campcard_pool_conf(camp_id, rand_time)
        res_err, card = self.randcard_frompool( pool_conf )
        if res_err:
            log.error('No camp randcard pool. cid:{0}, camp_id:{1}, rand_time:{2}.'.format( self.cid, camp_id, rand_time ))
            defer.returnValue( res_err )
        # 扣钻石
        yield self.user.consume_credits( need_credits, WAY_CAMP_RANDCARD )
        # 更新抽卡次数
        yield redis.hset(HASH_CAMPRAND_COMMON, self.cid, dumps([int(time()), curr_camp_data, next_camp_data]))
        # 新增伙伴
        try:
            new_fellows = []
            # args: fellow_id, is_major, camp_id, on_troop
            res_err, attrib = yield self.user.fellow_mgr.create_table_data( card['ItemID'], 0, 0, 0 )
            if not res_err:
                new_fellows.append( [attrib.attrib_id, card['ItemID']] )
                conf = get_fellow_by_fid( card['ItemID'] )
                if conf:
                    syslogger(LOG_FELLOW_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, attrib.attrib_id, card['ItemID'], conf['QualityLevel'], conf['Star'], WAY_CAMP_RANDCARD, '')
        except Exception as e:
            log.warn('Create fellow fail! e:', e)
            defer.returnValue(res_err)
        # 阵营抽卡抽到紫卡, 全服广播
        if card['Notice']:
            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_RANDCARD, [self.user.nick_name, RANDCARD_TYPE_CAMP, [card['ItemID']]]]]
            gw_broadcast('sync_broadcast', [message])

        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_16, 1)
        
        defer.returnValue( (self.user.credits, rand_time, new_fellows) )

    def left_purple_count(self, card_type, level, rand_count):
        '''
        @summary: 必抽取紫卡的剩余次数
        @param  : level-神坛等级
        @param  : rand_count-已抽卡的次数
        '''
        max_level    = get_randcard_max_level( card_type )
        next_level   = level + 1 if (level+1) < max_level else max_level
        next_max_cnt = get_randcard_level_count( next_level,  card_type )
        if rand_count > next_max_cnt:
            log.error('Shrine level error. shrine_level: {0}, rand_count: {1}.'.format( level, rand_count ))
            left_count = 0
        elif rand_count > 0:
            left_count = next_max_cnt - rand_count
        else:
            left_count = 0
        
        return left_count

    @defer.inlineCallbacks
    def randcard(self, card_type, rand_times):
        '''
        @return : err, credits, res_fellow_list
        '''
        res_err = REQUEST_LIMIT_ERROR

        shrine_data = yield redis.hget(HASH_SHRINE_TYPE % card_type, self.cid)
        if shrine_data:
            shrine_data = loads( shrine_data )
            if len(shrine_data) == 4:
                shrine_level, rand_count, last_free_time, last_purple_time = shrine_data
                first_blue, first_purple = 0, 0
            else:
                shrine_level, rand_count, last_free_time, last_purple_time, first_blue, first_purple = shrine_data
        else:
            shrine_level, rand_count, last_free_time, last_purple_time, first_blue, first_purple = 0, 0, 0, 0, 1, 1
        # 抽卡消耗的配置
        _consume = get_randcard_consume_conf( card_type )
        if not _consume:
            log.error('Can not find conf.')
            defer.returnValue( NOT_FOUND_CONF )

        # 距离下一场免费抽奖所需时间
        need_time = self.left_free_timestamp( last_free_time, _consume['FreeTime'] )
        # 检查道具或钻石是否充足
        user_credits = self.user.base_att.credits
        if (_consume['ItemType'] == ITEM_TYPE_MONEY):
            _rand_cost = _consume['ItemNum']*rand_times
            if rand_times > 1:
                # 无免费抽奖时所需钻石
                if (need_time > 0):
                    _rand_cost = int((_consume['ItemNum'] * 10 * RANDCARD_TEN_RATIO + 99) / 100)
                else:
                    _rand_cost = int((_consume['ItemNum'] * 9 * RANDCARD_TEN_RATIO + 99) / 100)

            # 无免费抽奖时钻石不足
            if (need_time > 0) and (_rand_cost > user_credits):
                log.error('Not enough credits. need: {0}, cur: {1}.'.format( _rand_cost, user_credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            # 有免费抽奖且是十连抽时钻石不足
            elif 0 >= need_time and rand_times > 1 and (_rand_cost > user_credits):
                log.error('Not enough credits. need: {0}, cur: {1}.'.format( _rand_cost, user_credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        elif (_consume['ItemType'] == ITEM_TYPE_ITEM): 
            total_num, item_attribs = yield self.user.bag_item_mgr.get_items( _consume['ItemID'] )
            # 情缘令不足
            if (_consume['ItemNum']*rand_times) > total_num:
                log.error('cur num: {0}.'.format( total_num ))
                defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
        else:
            log.error('Unknown item type: {0}.'.format( _consume['ItemType'] ))
            defer.returnValue( RANDCARD_TYPE_ERROR )
        # 获取抽卡池
        first_flag = 0
        if card_type  == CARD_SHRINE_BLUE:
            first_flag = first_blue
        elif card_type == CARD_SHRINE_PURPLE:
            first_flag = first_purple
        pool = self.get_randcard_pool( card_type, shrine_level, rand_count, need_time, last_purple_time, first_flag )
        if not pool:
            defer.returnValue( NOT_FOUND_CONF )
        # 无免费抽卡时更新状态位
        if need_time > 0 or (0 >= need_time and rand_times > 1):
            if card_type  == CARD_SHRINE_BLUE:
                if first_blue:
                    first_flag, first_blue = 0, 0
            elif card_type == CARD_SHRINE_PURPLE:
                if first_purple:
                    first_flag, first_purple = 0, 0
        # 抽卡并扣道具或者钻石
        items_return      = []
        card_fellow_ids   = [] # 抽卡抽到的fellow
        msg_fellow_ids    = [] # 走马灯公告的fellow
        cost_credits      = 0  # 主要是处理十连抽
        max_shrine_level  = get_randcard_max_level( card_type )
        for i in range(0, rand_times):
            res_err, card = self.randcard_frompool( pool )
            if res_err:
                defer.returnValue( res_err )
            # 消耗道具或者钻石
            if (_consume['ItemType'] == ITEM_TYPE_MONEY):
                if need_time > 0:
                    cost_credits += _consume['ItemNum']
            elif (_consume['ItemType'] == ITEM_TYPE_ITEM): 
                res_err, used_attribs = yield self.user.bag_item_mgr.use( _consume['ItemID'], 1 )
                if res_err:
                    log.error('Use item error.')
                    defer.returnValue( res_err )
                # used_attribs-已使用的道具
                for _a in used_attribs:
                    items_return.append( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num] )
            card_fellow_ids.append( card['ItemId'] )
            # 更新抽得紫卡的时间
            conf = get_fellow_by_fid( card['ItemId'] )
            if conf and conf['Quality'] == QUALITY_PURPLE:
                msg_fellow_ids.append( card['ItemId'] )
                last_purple_time = int(time())
            # 更新玩家的shrine数据, 含rand_count, shrine_level, 及shrine升级后更新pool
            shrine_level, rand_count, last_free_time = self.update_shrine( card_type, max_shrine_level, shrine_level, rand_count, last_free_time, _consume['FreeTime'] )
            need_time = self.left_free_timestamp( last_free_time, _consume['FreeTime'] )
            # 获取抽卡池
            pool = self.get_randcard_pool( card_type, shrine_level, rand_count, need_time, last_purple_time, first_flag )
        # 保存redis data
        yield redis.hset(HASH_SHRINE_TYPE % card_type, self.cid, dumps((shrine_level, rand_count, last_free_time, last_purple_time, first_blue, first_purple)))
        #log.info('For Test. rand fellow_ids: {0}.'.format( card_fellow_ids ))
        # 抽卡类型 用于广播、syslogger
        if card_type    == CARD_SHRINE_GREEN:
            _type_name  = RANDCARD_TYPE_GREEN
            _way_name   = WAY_RANDCARD_ITEM
        elif card_type  == CARD_SHRINE_BLUE:
            _type_name  = RANDCARD_TYPE_BLUE
            _way_name   = WAY_RANDCARD_BLUE
        elif rand_times == 10:
            _type_name  = RANDCARD_TYPE_TEN
            _way_name   = WAY_RANDCARD_TEN
        else:
            _type_name  = RANDCARD_TYPE_PURPLE
            _way_name   = WAY_RANDCARD_PURPLE

        if cost_credits:
            # 十连抽时打折
            if rand_times > 1:
                cost_credits = int((cost_credits * RANDCARD_TEN_RATIO + 99) / 100)
                msg = [12, [self.user.nick_name, self.user.lead_id]]
                gw_broadcast('sync_broadcast',[[3, msg]] )
            yield self.user.consume_credits( cost_credits, _way_name )
        # 新增fellow
        new_fellows = []
        for _id in card_fellow_ids:
            try:
                # args: fellow_id, is_major, camp_id, on_troop
                res_err, attrib = yield self.user.fellow_mgr.create_table_data( _id, 0, 0, 0 )
                if not res_err:
                    new_fellows.append( [attrib.attrib_id, _id] )
                    conf = get_fellow_by_fid( _id )
                    if conf:
                        syslogger(LOG_FELLOW_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, attrib.attrib_id, _id, conf['QualityLevel'], conf['Star'], _way_name, '')
            except Exception as e:
                log.warn('Create fellow fail! e:', e)
                defer.returnValue(res_err)
        # 情缘抽到紫卡, 全服广播
        if msg_fellow_ids:
            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_RANDCARD, [self.user.base_att.nick_name, _type_name, msg_fellow_ids]]]
            gw_broadcast('sync_broadcast', [message])

        for _item in items_return:
            syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _item[0], _item[2], 1, WAY_RANDCARD_ITEM)

        status = yield self.status()
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_16, 1)
        defer.returnValue( (self.user.base_att.credits, new_fellows, status[0], status[1], status[2], status[3], items_return) )
 
    def update_shrine( self, card_type, max_level, level, count, last_free_time, free_time ):
        count += 1
        cur_time     = int(time())
        next_level   = level + 1 if (level+1) < max_level else max_level
        next_max_cnt = get_randcard_level_count( next_level,  card_type)
        if card_type in (CARD_SHRINE_BLUE, CARD_SHRINE_PURPLE):
            if (cur_time - last_free_time) > free_time:
                last_free_time = cur_time
        if count >= next_max_cnt:
            # 神坛已经升级到最高等级
            if level >= max_level:
                count = 0
            elif next_max_cnt:
                level = next_level
                count = 0

        return level, count, last_free_time

    def left_free_timestamp(self, last_free_time, rand_free_time):
        '''
        @summary: 免费抽奖的倒计时剩余时间
        @param  : last_free_time-上次免费抽奖的时间, 0代表还未免费抽过奖
        @param  : rand_free_time-免费抽奖时间的周期
        @param  : need_time-距离下一次免费抽奖还需要的时间
        '''
        need_time = -1
        if last_free_time:
            need_time = int(last_free_time + rand_free_time - time())
            if need_time < 0:
                need_time = 0
 
        return need_time

    def get_randcard_pool(self, card_type, shrine_level, rand_count, need_time, last_purple_time, first_flag=0):
        '''
        @summary: 获取抽卡池
        '''
        pool_level = 0
        if card_type == CARD_SHRINE_GREEN:
            if rand_count == 0:
                pool_level = shrine_level + 1
        # 新玩家第一次消耗钻石抽卡时 读取shrine_level+1的配置
        elif first_flag:
            pool_level = shrine_level + 1
        elif need_time == -1: # 第一次免费抽卡
            pool_level = shrine_level + 1
        else:
            # 玩家两次紫卡抽取时间大于4天（96小时）则默认读取shrine_level+1的配置
            if last_purple_time and (int(time() - last_purple_time) >  345600): # 4*24
                pool_level = shrine_level + 1

            # 累积抽卡次数=0的时候，读取当前shrine_level+1配置
            if rand_count == 0:
                if pool_level > 0:
                    pool_level += 1
                else:
                    pool_level = shrine_level + 1

        # 随机时，读取最接近神坛等级(pool_level)的配置
        all_shrine_level = get_cardpool_shrine_levels( card_type )
        # 读cardpool时, 最终的神坛等级
        final_level = 0
        for _level in all_shrine_level:
            if _level <= pool_level and final_level < _level:
                final_level = _level
 
        # 随机时，读取最接近玩家等级的配置
        all_start_level = get_cardpool_start_levels(card_type, final_level)
        # 读cardpool时, 最终的start等级
        start_level = 1
        for _level in all_start_level:
            if _level <= self.user.base_att.level and start_level < _level:
                start_level = _level
        return get_cardpool_conf( card_type, final_level, start_level )

    def randcard_frompool(self, pool):
        '''
        @summary: 从抽卡池中抽卡
        '''
        _total_rate = 0
        for _conf in pool.itervalues():
            _total_rate += _conf['Rate']

        if _total_rate <= 0:
            log.warn('There is no cardpool. _total_rate: {0}.'.format( _total_rate ))
            return (NOT_FOUND_CONF, {})

        _curr_rate = 0
        _randint   = rand_num(_total_rate)
        for _conf in pool.itervalues():
            if _randint < (_curr_rate + _conf['Rate']):
                #log.error('For Test. _randint: {0}, _curr_rate: {1}, _conf_rate: {2}.'.format( _randint, _curr_rate, _conf['Rate'] ))
                return (NO_ERROR, _conf)
            else:
                _curr_rate += _conf['Rate']
        else:
            log.warn('There is no cardpool. _randint: {0}, _total_rate: {1}.'.format( _randint, _total_rate ))
            return (NOT_FOUND_CONF, {} )

 
WAY_TO_ITEM_TYPE = {
         1: WAY_SHOP_GOLD,
         2: WAY_EXP_PANDA,
         3: WAY_CHEST_GOLD,
         4: WAY_KEY_GOLD,
         5: WAY_CHEST_SILVER,
         6: WAY_KEY_SILVER,
         6: WAY_CHEST_BRONZE,
         7: WAY_KEY_BRONZE,
         8: WAY_ENERGY_WAN,
         9: WAY_BINGLIANG_WAN,
        }

class GSItemShopMgr(object):
    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        # 限购商品上次购买的时间
        self.last_buyed_time  = 0
        # data format: {item_id: item_num, ...}
        self.last_buyed_items = None

    @defer.inlineCallbacks
    def _load(self):
        if self.last_buyed_items is None:
            self.last_buyed_items = {}
            _data = yield redis.hget( HASH_ITEM_SHOP_RECORD, self.cid )
            if _data:
                _last_buyed_time, _buyed_items = loads( _data )
                _reset_timestamp = get_reset_timestamp()
                if _last_buyed_time <= _reset_timestamp:
                    _buyed_items = []
                self.last_buyed_time = _last_buyed_time
                for _id, _num in _buyed_items:
                    self.last_buyed_items[_id] = _num
        else:
            _reset_timestamp = get_reset_timestamp()
            if self.last_buyed_time <= _reset_timestamp:
                self.last_buyed_items = {}
 
    @defer.inlineCallbacks
    def sync_record(self):
        if self.last_buyed_time and self.last_buyed_items:
            _buyed_items = []
            for _id, _num in self.last_buyed_items.iteritems():
                _buyed_items.append( [_id, _num] )
            yield redis.hset( HASH_ITEM_SHOP_RECORD, self.cid, dumps( (self.last_buyed_time, _buyed_items) ) )

    @defer.inlineCallbacks
    def get_record(self):
        yield self._load()
        _buyed_items = []
        for _id, _num in self.last_buyed_items.iteritems():
            _buyed_items.append( [_id, _num] )
        defer.returnValue( _buyed_items )

    @defer.inlineCallbacks
    def buy_item(self, shop_item_id, item_num):
        '''
        @param : shop_item_id-商城商品ID item_num-商城商品数量
        '''
        yield self._load()
        # 判断是否限购
        _conf = get_item_shop_conf( shop_item_id )
        if not _conf:
            log.error('Can not find shop id conf. shop item id: {0}.'.format( shop_item_id ))
            defer.returnValue( NOT_FOUND_CONF )

        _buyed_count = 0
        if _conf['ItemLimitNum'] > 0: # 限购
            _vip_level = self.user.base_att.vip_level
            _limit_num = _conf['ItemLimitNum'] + _vip_level * _conf['ItemIncrease']
            _buyed_count += self.last_buyed_items.get(shop_item_id, 0)
            if (_buyed_count + item_num) >  _limit_num:
                log.error('_buyed_count: {0}, _limit_num: {1}.'.format( _buyed_count, _limit_num ))
                defer.returnValue( SHOP_ITEM_MAX_NUM )

        # 判断宝石数量
        _cost = 0
        if _conf['CostItemType'] == ITEM_TYPE_MONEY and _conf['CostItemID'] == 2:
            _cost = (_conf['CostItemNum'] * item_num + (item_num*(item_num-1)/2 + _buyed_count*item_num) * _conf['CostItemIncrease'])
            if _cost > self.user.base_att.credits:
                log.error('user credits. need: {0}, cur: {1}.'.format( _cost, self.user.base_att.credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        else:
            log.error('unknown cost item. _conf: {0}.'.format( _conf ))
            defer.returnValue( ITEM_TYPE_ERROR )

        # 扣钻石
        if _cost > 0:
            add_type = WAY_TO_ITEM_TYPE.get(shop_item_id, WAY_ITEM_SHOP)
            yield self.user.consume_credits( _cost, add_type )

        # 向背包中新增道具
        model = ITEM_MODELs.get( _conf['ItemType'], None )
        if not model:
            log.error('Can not find model. item type: {0}.'.format( _conf['ItemType'] ))
            defer.returnValue( ITEM_TYPE_ERROR )
        way_others = str((shop_item_id, item_num))
        res_err, add_items = yield model( self.user, ItemID=_conf['ItemID'], ItemNum=(item_num * _conf['ItemNum']), AddType=WAY_ITEM_SHOP, WayOthers=way_others, CapacityFlag=False )
        syslogger(LOG_SHOP_BUY, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _conf['ItemID'], item_num * _conf['ItemNum'])
        if res_err:
            defer.returnValue( res_err )

        if _conf['ItemLimitNum'] > 0: # 限购
            self.last_buyed_time = int(time())
            self.last_buyed_items[shop_item_id] = item_num + _buyed_count
            yield self.sync_record()
        if shop_item_id == 8:
            num = item_num if 0 < item_num <= 3 else 3
            yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_17, num)
        if shop_item_id == 9:
            num = item_num if 0 < item_num <= 3 else 3
            yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_18, num)
        defer.returnValue( (shop_item_id, self.last_buyed_items.get(shop_item_id, 0), self.user.base_att.credits, add_items) )


class VipPackageMgr:
    '''
    @summary: 商店之VIP礼包
    '''

    @staticmethod
    @defer.inlineCallbacks
    def buyed_package( cid ):
        data = yield redis.hget( HASH_VIP_PACKAGE_RECORD, cid )
        if data:
            data = loads( data )
        else:
            data = []
 
        defer.returnValue( data )

    @staticmethod
    @defer.inlineCallbacks
    def buy_package( user, vip_level ):
        # 检查玩家VIP等级是否满足
        if vip_level > user.base_att.vip_level:
            log.error('buy limit. buy level: {0}, cur level: {1}.'.format( vip_level, user.base_att.vip_level ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 检查已购买记录
        buyed_record = yield VipPackageMgr.buyed_package( user.cid )
        if vip_level in buyed_record:
            log.error('The vip package had buyed. vip_level: {0}.'.format( vip_level ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 检查钻石是否充足
        conf = get_vip_package( vip_level )
        if not conf:
            log.error('Unknown vip package. vip_level: {0}.'.format( vip_level ))
            defer.returnValue( NOT_FOUND_CONF )
        if conf['PresentPrice'] > user.base_att.credits:
            log.error('credits. need: {0}, cur: {1}.'.format( conf['PresentPrice'], user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        # 扣钻石
        yield user.consume_credits( conf['PresentPrice'], WAY_VIP_PACKAGE_SHOP )

        # 新增购买记录
        buyed_record.append( vip_level )
        yield redis.hset( HASH_VIP_PACKAGE_RECORD, user.cid, dumps(buyed_record) )
        # 礼包道具进背包
        model = ITEM_MODELs.get( conf['ItemType'], None )
        if not model:
            log.error('Unknown item type. item : {0}.'.format( (conf['ItemType'], conf['ItemID']) ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )
        way_others = str((vip_level,))
        res_err, items_return = yield model( user, ItemID=conf['ItemID'], ItemNum=1, AddType=WAY_VIP_PACKAGE_SHOP, WayOthers=way_others, CapacityFlag=False )
        syslogger(LOG_SHOP_BUY, user.cid, user.level, user.vip_level, user.alliance_id, conf['ItemID'], 1)
        if res_err:
            log.error('Add package item error. conf: {0}.'.format( conf ))
            defer.returnValue( res_err )

        defer.returnValue( (vip_level, user.base_att.credits, items_return) )




