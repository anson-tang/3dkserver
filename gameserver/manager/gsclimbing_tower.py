#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from datetime import datetime
from time     import time
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from utils    import datetime2string, string2datetime, timestamp_is_today
from system   import get_vip_conf, get_climbing_conf, get_all_climbing_layer

from twisted.internet       import defer, reactor
from models.award_center    import g_AwardCenterMgr
from models.item            import *
from models.characterserver import gs_load_table_data, gs_create_table_data
from manager.gsattribute    import GSAttribute
from table_fields           import TABLE_FIELDS
from handler.character      import gs_offline_login, gs_offline_logout


@defer.inlineCallbacks
def load_climbing_user_data(cid):
    ''' 
    @summary: 加载玩家的基本信息。
    '''
    _user_data = []
    _offline_user = yield gs_offline_login( cid )
    if _offline_user:
        _ = yield _offline_user.climbing_tower_mgr.climbing_data()
        _alliance_info = (_offline_user.alliance_id, _offline_user.alliance_name)
        _user_data = [cid, _offline_user.lead_id, _offline_user.level, _offline_user.nick_name, _offline_user.might, _alliance_info]
        reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, cid)

    defer.returnValue( _user_data )



class GSClimbingMgr(object):
    '''
    @summary: 天外天
    '''
    _table = 'climbing_tower'
    _fields = TABLE_FIELDS['climbing_tower'][0]

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        self.load_flag     = False 

        all_climbing_layers = get_all_climbing_layer()
        self.MAX_LAYER      = max(all_climbing_layers) if all_climbing_layers else 0
        self.climbing       = GSAttribute(user.cid, GSClimbingMgr._table, user.cid)

    @defer.inlineCallbacks
    def load(self):
        if self.load_flag:
            defer.returnValue( None )

        try:
            table_data = yield gs_load_table_data(self.cid, GSClimbingMgr._table)
            # 注意在收到返回消息后才能赋值
            self.load_flag = True

            if table_data:
                table_data = dict(zip(GSClimbingMgr._fields, table_data))
                self.climbing.updateGSAttribute( False, **table_data )
            else:
                yield self.new()
        except Exception as e:
            log.error( 'Exception raise. e: {0}.'.format( e ))

    def sync_to_cs(self):
        if self.climbing:
            self.climbing.syncToCS()

    @defer.inlineCallbacks
    def new(self):
        init_data = [self.cid, 1, 0, 0, 0, 0, 0, 0, 0, int(time())]
        kwargs = dict(zip(GSClimbingMgr._fields[1:], init_data))
        create_data = yield gs_create_table_data(self.cid, GSClimbingMgr._table, **kwargs)
        if create_data:
            create_data = dict(zip(GSClimbingMgr._fields, create_data))
            self.climbing.updateGSAttribute( False, **create_data )
        else: # 新增数据失败
            self.load_flag = False
 
    def system_daily_reset(self):
        '''
        @summary: 每天24点系统重置天外天数据
        '''
        # 不是同一天, 系统重置玩家数据
        dt_now  = datetime.now()
        dt_last = self.climbing.last_datetime
        if dt_now.date() != dt_last.date():
            self.climbing.free_fight     = 0 
            self.climbing.free_reset     = 0
            self.climbing.left_buy_reset = 0
            self.climbing.last_datetime  = dt_now

    def get_vip_conf_of_climbing(self):
        conf = get_vip_conf( self.user.vip_level )
        max_free_fight  = conf['TowerFightCount'] if conf else 0
        left_free_fight = max_free_fight - self.climbing.free_fight if max_free_fight > self.climbing.free_fight else 0
        max_free_reset  = conf['TowerResetCount'] if conf else 0
        left_free_reset = max_free_reset - self.climbing.free_reset if max_free_reset > self.climbing.free_reset else 0
        max_buy_reset   = conf['TowerBuyReset'] if conf else 0
        left_buy_reset  = max_buy_reset - self.climbing.left_buy_reset if max_buy_reset > self.climbing.left_buy_reset else 0

        return [left_free_fight, left_free_reset, left_buy_reset, max_free_fight, max_free_reset, max_buy_reset]

    @defer.inlineCallbacks
    def climbing_data(self):
        '''
        @summary: 天外天的基本信息
        '''
        yield self.load()
        self.system_daily_reset()

        climbing_data = self.get_vip_conf_of_climbing()
        defer.returnValue( (self.climbing.cur_layer, self.climbing.max_layer, climbing_data[0]+self.climbing.buyed_fight, \
                climbing_data[1]+self.climbing.buyed_reset, climbing_data[2], self.climbing.start_datetime, self.user.credits) )

    @defer.inlineCallbacks
    def reset_climbing(self):
        '''
        @summary: 重置天外天数据。当前塔层归1, 挑战次数置满, 更新last_time, 扣重置次数
        '''
        self.system_daily_reset()
        # 正在扫荡, 不能重置
        if self.climbing.start_datetime > 0:
            log.error('In climbing could not reset.')
            defer.returnValue( IN_CLIMBING_ONGOING )
        if self.climbing.cur_layer == 1:
            log.error('Tower layer 1 could not reset.')
            defer.returnValue( IN_CLIMBING_MIN_LAYER )
        climbing_data = self.get_vip_conf_of_climbing()
        if (climbing_data[1] + self.climbing.buyed_reset < 1):
            log.warn('User no reset count. cid: {0}, had_free_reset: {1}, buyed_reset: {2}.'.format( self.cid, self.climbing.free_reset, self.climbing.buyed_reset ))
            res_err = yield self.buy_count(1)
            if isinstance(res_err, int):
                defer.returnValue( res_err )
            climbing_data = self.get_vip_conf_of_climbing()

        self.climbing.cur_layer = 1
        if self.climbing.buyed_reset > 0:
            self.climbing.buyed_reset -= 1
        elif climbing_data[1] > 0:
            self.climbing.free_reset += 1
            climbing_data[1] -= 1

        self.climbing.free_fight    = 0
        self.climbing.last_datetime = datetime.now()
 
        defer.returnValue( (self.climbing.cur_layer, self.climbing.max_layer, climbing_data[3]+self.climbing.buyed_fight, \
                climbing_data[1]+self.climbing.buyed_reset, climbing_data[2], self.climbing.start_datetime, self.user.credits) )

    @defer.inlineCallbacks
    def buy_count(self, count_type):
        '''
        @summary: 购买重置/挑战 次数, 购买前检查上次次数更新时的时间, 重置次数有购买限制, 和VIP level相关。
                count_type: 1:购买重置次数; 2:购买挑战次数
        '''
        res_err = UNKNOWN_ERROR
        self.system_daily_reset()
        climbing_data = self.get_vip_conf_of_climbing()
        if count_type == 1:
            if (climbing_data[1] + self.climbing.buyed_reset > 0):
                log.error('User has reset count. cid: {0}, had_free_reset: {1}, buyed_reset: {2}.'.format( self.cid, self.climbing.free_reset, self.climbing.buyed_reset ))
                defer.returnValue( HAVE_NUM_TO_USE )
            if climbing_data[2] < 1:
                log.error('Daily max buy reset count limit. cid: {0}.'.format( self.cid ))
                defer.returnValue( BUY_MAX_NUM_ERROR )
            if self.climbing.cur_layer < self.climbing.max_layer:
                reset_layer = self.climbing.cur_layer
            else:
                reset_layer = self.climbing.max_layer
            conf = get_climbing_conf( reset_layer )
            if not conf:
                log.error('No conf. cid: {0}, reset_layer: {0}.'.format( cid, reset_layer ))
                defer.returnValue( NOT_FOUND_CONF )
            if conf['ResetCost'] > self.user.base_att.credits:
                log.error('Credits not enough. need: {0}, cur: {1}.'.format( conf['ResetCost'], self.user.base_att.credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            yield self.user.consume_credits( conf['ResetCost'], WAY_CLIMBING_RESET )
            self.climbing.left_buy_reset += 1
            self.climbing.buyed_reset    += 1
            res_err = count_type, self.climbing.buyed_reset, self.user.base_att.credits
        elif count_type == 2:
            if (climbing_data[0] + self.climbing.buyed_fight > 0):
                log.error('User has fight count. cid: {0}, had_free_fight: {1}, buyed_fight: {2}.'.format( self.cid, self.climbing.free_fight, self.climbing.buyed_fight ))
                defer.returnValue( HAVE_NUM_TO_USE )
            if CLIMBING_FIGHT_COST > self.user.base_att.credits:
                log.error('Credits not enough. need: 10, cur: {0}.'.format( self.user.base_att.credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            yield self.user.consume_credits( CLIMBING_FIGHT_COST, WAY_CLIMBING_FIGHT )
            self.climbing.buyed_fight += 1
            res_err = count_type, self.climbing.buyed_fight, self.user.base_att.credits

        defer.returnValue( res_err )
 
    @defer.inlineCallbacks
    def climbing_reward(self, fight_layer, status):
        '''
        @summary: 单次通关失败扣挑战次数, 更新玩家当前所在塔层及最大塔层, 给通关后的奖励
        '''
        self.system_daily_reset()
        # 可挑战的塔层数据不同步
        if fight_layer != self.climbing.cur_layer:
            log.error('User request fight_layer error. cid: {0}, fight_layer: {1}, cur_layer: {2}.'.format( self.cid, fight_layer, self.climbing.cur_layer ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 没有挑战次数不能挑战
        climbing_data = self.get_vip_conf_of_climbing()
        if (climbing_data[0] + self.climbing.buyed_fight < 1):
            log.error('User no fight count. cid: {0}, had_free_fight: {1}, buyed_fight: {2}.'.format( self.cid, self.climbing.free_fight, self.climbing.buyed_fight ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 已经到了最大塔层 不能继续挑战
        if self.climbing.cur_layer >= self.MAX_LAYER:
            log.error('Had been the max layer. cur_layer: {0}, climbing_tower MAX_LAYER: {1}.'.format( self.climbing.cur_layer, self.MAX_LAYER ))
            defer.returnValue( IN_CLIMBING_MAX_LAYER )
        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_9, 1 )
        yield self.user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_10, self.climbing.cur_layer)
        #成就
        yield self.user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_10, self.climbing.cur_layer)
        if not status: # 通关失败
            if self.climbing.buyed_fight > 0:
                self.climbing.buyed_fight -= 1
            elif climbing_data[0] > 0:
                climbing_data[0] -= 1
                self.climbing.free_fight += 1
            defer.returnValue( (status, self.climbing.cur_layer, self.climbing.max_layer, climbing_data[0]+self.climbing.buyed_fight, [], 0, 0, 0, self.user.base_att.energy) )
 
        # 获取塔层通过的奖励
        conf = get_climbing_conf( self.climbing.cur_layer )
        if not conf:
            log.error('No conf. cid: {0}, cur_layer: {0}.'.format( cid, self.climbing.cur_layer ))
            defer.returnValue( NOT_FOUND_CONF )

        #self.user.base_att.golds += conf['RewardGold']
        self.user.get_golds( conf['RewardGold'], WAY_CLIMBING_AWARD )
        self.user.base_att.soul  += conf['RewardSoul']
        items_return = []
        #log.info('For Test. cur_layer: {0}, BonusList: {1}.'.format( self.climbing.cur_layer, conf['BonusList'] ))
        for _type, _id, _num in conf['BonusList']:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. item: {0}.'.format( (_type, _id, _num) ))
                continue
            res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_CLIMBING_AWARD, CapacityFlag=False)
            if not res_err and value:
                #log.info('For Test. value: {0}.'.format( value ))
                for _v in value:
                    items_return = total_new_items( _v, items_return )
        #log.info('For Test. after BonusList: {0}.'.format( conf['BonusList'] ))

        if self.climbing.cur_layer >= self.MAX_LAYER:
            self.climbing.cur_layer = self.MAX_LAYER
        else:
            self.climbing.cur_layer += 1

        # 挑战更高的塔层
        if (self.climbing.cur_layer <= self.MAX_LAYER) and (self.climbing.cur_layer > self.climbing.max_layer):
            self.climbing.max_layer += 1
        if self.climbing.max_layer > self.MAX_LAYER:
            self.climbing.max_layer = self.MAX_LAYER

        # 更新天外天排行榜
        yield redis.zadd(SET_CLIMBING_CID_LAYER, self.cid, -self.climbing.max_layer)

        defer.returnValue( (status, self.climbing.cur_layer, self.climbing.max_layer, climbing_data[0]+self.climbing.buyed_fight, items_return, conf['RewardGold'], conf['RewardSoul'], 0, self.user.base_att.energy) )

    def start_climbing(self, start_layer):
        '''
        @summary: 记录扫荡的开始时间
        '''
        # 塔层数据不同步
        if start_layer != self.climbing.cur_layer:
            log.error('User request start_layer error. cid: {0}, start_layer: {1}, cur_layer: {2}.'.format( self.cid, start_layer, self.climbing.cur_layer ))
            return REQUEST_LIMIT_ERROR

        if self.climbing.cur_layer > self.climbing.max_layer:
            log.error('Could not climbing. cur_layer: {0}, max_layer: {1}.'.format( self.climbing.cur_layer, self.climbing.max_layer ))
            return IN_CLIMBING_MAX_LAYER
        self.climbing.start_datetime = int(time())
 
        return NO_ERROR

    @defer.inlineCallbacks
    def stop_climbing(self, stop_layer):
        '''
        @summary: 根据结束时间计算可扫荡到的塔层, 奖励进领奖中心。
        '''
        timestamp     = int(time())
        total_sceonds = timestamp - self.climbing.start_datetime
        if (not self.climbing.start_datetime) or (total_sceonds <= 0):
            log.error('Unknown error. start climbing time: {0}, cur_layer: {1}, stop_layer: {2}, total_sceonds: {3}.'.format( self.climbing.start_datetime, self.climbing.cur_layer, stop_layer, total_sceonds ))
            defer.returnValue( IN_CLIMBING_DONE )
        # 重置扫荡的开始时间
        self.climbing.start_datetime = 0

        #log.info('For Test. cur_layer: {0}, stop_layer: {1}, total_sceonds: {2}.'.format( self.climbing.cur_layer, stop_layer, total_sceonds ))
        flag = True
        award_layer = [] # 可获得奖励的塔层列表
        while flag:
            conf = get_climbing_conf( self.climbing.cur_layer )
            if not conf:
                log.error('No conf. tower layer: {0}.'.format( self.climbing.cur_layer ))
                defer.returnValue( NOT_FOUND_CONF )

            if total_sceonds < conf['NeedTime']:
                flag = False
            else:
                total_sceonds -= conf['NeedTime']
                # 奖励进领奖中心
                award_layer.append( self.climbing.cur_layer )
                # 判断是否已经到达了conf的最高层
                if self.climbing.cur_layer >= self.MAX_LAYER:
                    flag = False
                    self.climbing.cur_layer = self.MAX_LAYER
                else:
                    if self.climbing.cur_layer >= self.climbing.max_layer:
                        flag = False
                    self.climbing.cur_layer += 1
                # 每日任务计数
                yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_9, 1 )
            #log.info('For Test. cur_layer: {0}, stop_layer: {1}, total_sceonds: {2}, flag: {3}.'.format( self.climbing.cur_layer, stop_layer, total_sceonds, flag ))

        if award_layer:
            yield g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_CLIMBING, [timestamp, award_layer] )
 
        defer.returnValue( (self.climbing.cur_layer, self.climbing.max_layer) )

    @defer.inlineCallbacks
    def finish_climbing(self, start_layer):
        '''
        @summary: 使用钻石购买扫荡到最高塔层的时间, 更新玩家当前所在塔层及最大塔层, 给通关后的奖励
        '''
        if start_layer > self.climbing.max_layer:
            log.error('Could not climbing. cur_layer: {0}, start_layer: {1}, max_layer: {2}.'.format( self.climbing.cur_layer, start_layer, self.climbing.max_layer ))
            defer.returnValue( IN_CLIMBING_MAX_LAYER )
 
        award_layer   = [] # 可获得奖励的塔层列表
        total_credits = 0  # 需要消耗的钻石
        finish_layer  = start_layer # self.climbing.cur_layer
        while finish_layer <= self.climbing.max_layer:
            conf = get_climbing_conf( finish_layer )
            if not conf:
                log.error('No conf. tower layer: {0}.'.format( finish_layer ))
                defer.returnValue( NOT_FOUND_CONF )
            total_credits += conf['NeedTime']
            award_layer.append( finish_layer )
            finish_layer += 1
        if (total_credits % COOLDOWN_TIME_COST):
            total_credits = (total_credits / COOLDOWN_TIME_COST) + 1
        else:
            total_credits = (total_credits / COOLDOWN_TIME_COST)

        if total_credits > self.user.base_att.credits:
            log.error('Credits not enough. need: {0}, cur: {1}.'.format( total_credits, self.user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        # 重置扫荡的开始时间
        self.climbing.start_datetime = 0

        self.climbing.cur_layer = finish_layer
        yield self.user.consume_credits( total_credits, WAY_CLIMBING_DONE )
        if award_layer:
            g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_CLIMBING, [int(time()), award_layer] )
            # 每日任务计数
            yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_9, len(award_layer) )
 
        defer.returnValue( (self.climbing.cur_layer, self.climbing.max_layer, self.user.base_att.credits) )
 
    @defer.inlineCallbacks
    def ranklist(self):
        ''' 获取天外天的排行榜 '''
        yield self.load()
        # get myself rank and layer
        _my_rank  = yield redis.zrank(SET_CLIMBING_CID_LAYER, self.cid)
        _my_rank  = 0 if _my_rank is None else int(_my_rank)+1
        _ranklist = [self.climbing.max_layer, _my_rank, []]

        _cid_layers = yield redis.zrange(SET_CLIMBING_CID_LAYER, 0, 9, withscores=True)
        for _idx, _data in enumerate(_cid_layers):
            #log.error('For Test. _idx: {0}, _cid_layers: {1}.'.format( _idx+1, _data ))
            if int(_data[1]) >= 0:
                continue
            _detail = yield load_climbing_user_data(_data[0])
            if not _detail:
                log.error('Unknown user. cid: {0}.'.format( _data[0] ))
                continue
            _detail.extend( [-int(_data[1]), _idx+1] )
            _ranklist[2].append( _detail )

        defer.returnValue( _ranklist )



