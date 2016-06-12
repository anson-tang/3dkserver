#!/usr/bin/env python
#-*-coding: utf-8-*-


from time     import time, localtime, strftime
from datetime import datetime, timedelta
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps
from utils    import datetime2time, get_next_timestamp, timestamp_is_today
from syslogger import syslogger
from random   import randint

from table_fields                import TABLE_FIELDS
from twisted.internet            import defer, reactor
from system                      import get_roleexp_by_level, get_vip_conf, get_chaos_conf, \
        get_vip_chargelist_conf, get_eat_peach_conf, get_monthly_card_conf, get_growth_plan_conf, \
        get_vip_welfare_conf, get_pay_activity_conf, get_pay_activity_award_conf, \
        get_consume_activity_conf, get_consume_activity_award_conf, get_excite_activity_conf, \
        get_max_role_level, get_lucky_turntable_conf, get_grow_server_reward_conf, get_grow_server_conf,\
        get_grow_server_conf, get_function_open_conf, get_game_limit_value, get_new_msg_conf
from protocol_manager            import cs_call, ms_send, alli_send, gw_broadcast

from models.award_center         import g_AwardCenterMgr
from models.constellation        import Constellation
from manager.gsattribute         import GSAttribute
from manager.gsfellow_new        import GSFellowMgr
from manager.gsbag_fellowsoul    import GSBagFellowsoulMgr
from manager.gsbag_item          import GSBagItemMgr
from manager.gsbag_treasure      import GSBagTreasureMgr
from manager.gsbag_equip         import GSBagEquipMgr
from manager.gsbag_equipshard    import GSBagEquipshardMgr
from manager.gsbag_jade          import GSBagJadeMgr
from manager.gsshop              import GSItemShopMgr
from manager.gsdecomposition     import GSDecompositionMgr, GSRebornMgr

from manager.gsbag_treasureshard import GSBagTreasureShardMgr

from manager.gsscene_new         import GSSceneMgr
from manager.gsexcite_activity   import GSExciteActivityMgr
from manager.gsmystical_shop     import GSMysticalShopMgr
from manager.gsclimbing_tower    import GSClimbingMgr
from manager.gsatlaslist         import GSAtlaslistMgr
from manager.gselitescene        import GSEliteSceneMgr
from manager.gsactivescene       import GSActiveSceneMgr
from manager.gsgoodwill          import GSGoodwillMgr
from manager.gsdaily_quest       import GSDailyQuestMgr

from models.item                 import ITEM_MODELs, total_new_items
from models.daily_pay            import add_daily_pay_record, get_daily_pay_record
from models.randpackage          import package_open
from manager.gsopen_server_activity import OpenServerActivityMgr
from manager.gsachievement       import GSAchievementMgr


class GSCharacter(object):
    _table    = 'character'
    _fields   = TABLE_FIELDS['character'][0]
    # 玩家下线时需要删除的对象list
    _del_attr = [ 'item_shop_mgr', 'excite_activity_mgr', 'decomposition_mgr', \
            'reborn_mgr', 'fellow_mgr', 'bag_fellowsoul_mgr', 'bag_item_mgr', \
            'bag_treasure_mgr', 'bag_treasureshard_mgr', 'bag_equip_mgr', \
            'bag_equipshard_mgr', 'scene_mgr', 'climbing_tower_mgr', \
            'constellation_mgr', 'atlaslist_mgr', 'goodwill_mgr', \
            'daily_quest_mgr', 'bag_jade_mgr', 'open_server_mgr','achievement_mgr']

    def __init__(self, cid):
        self.cid = cid
        self.base_att = GSAttribute(cid, GSCharacter._table, cid)
        # 获取离线玩家数据的标志位 True-离线登陆 False-正常登陆
        self.offline_flag = False
        # 离线登陆的个数
        self.offline_num = 0
        # 玩家的公会ID, 0-没有公会
        self.alliance_id = 0
        self.alliance_name = ''
        # 玩家的小伙伴管理
        self.fellow_mgr = GSFellowMgr(self)
        #self.fellow_mgr = GSFellowManager(cid)
        # 分魂背包
        self.bag_fellowsoul_mgr = GSBagFellowsoulMgr(self)
        # 道具背包
        self.bag_item_mgr       = GSBagItemMgr(self)
        # 宝物背包
        self.bag_treasure_mgr   = GSBagTreasureMgr(self)
        # 宝物碎片背包
        self.bag_treasureshard_mgr = GSBagTreasureShardMgr(self)
        # 装备背包
        self.bag_equip_mgr      = GSBagEquipMgr(self)
        # 装备碎片背包
        self.bag_equipshard_mgr = GSBagEquipshardMgr(self)
        # 玉魄背包
        self.bag_jade_mgr   = GSBagJadeMgr(self)
        # 副本
        self.scene_mgr = GSSceneMgr( self )
        # 精英副本
        self.elitescene_mgr = GSEliteSceneMgr( self )
        # 活动副本
        self.activescene_mgr = GSActiveSceneMgr( self )
        # 天外天
        self.climbing_tower_mgr = GSClimbingMgr(self)
        # 图鉴
        self.atlaslist_mgr = GSAtlaslistMgr( self )
        # 好感度
        self.goodwill_mgr = GSGoodwillMgr( self )
        
        #观星
        self.constellation_mgr = None
        # 每日任务
        self.daily_quest_mgr = GSDailyQuestMgr( self )
        #开服七日
        self.open_server_mgr = OpenServerActivityMgr(self)
        #成就
        self.achievement_mgr = GSAchievementMgr(self)
        # 已完成的对话组列表
        self.__finished_group = None
        #reactor.addSystemEventTrigger('before', 'shutdown', self.syncRedisData)

    def logout(self):
        ''' 玩家下线 '''
        log.debug('gscharacter logout. delete all attribute.')
        if hasattr(self, 'constellation_mgr') and self.constellation_mgr:
            self.constellation_mgr.sync()

        syslogger(LOG_LOGOUT, self.cid, self.cid, self.level, self.vip_level)
        for _attr in GSCharacter._del_attr:
            if hasattr(self, _attr) and self.__dict__.has_key(_attr):
                del self.__dict__[_attr]

    def logoutOffline(self):
        ''' 处理离线登陆的玩家 '''
        if self.offline_num > 1:
            self.offline_num -= 1
            return False
        else:
            self.offline_num = 0
            return True

    @defer.inlineCallbacks
    def syncRedisData(self):
        #if hasattr(self, 'constellation_mgr') and self.constellation_mgr:
        #    yield self.constellation_mgr.sync()
        #    log.info('For Test. redis sync... ...')
        pass

    def syncGameDataToCS(self):
        ''' sync Gameserver data to CharacterServer '''
        for _attr in GSCharacter._del_attr:
            mgr = self.__dict__.get(_attr, None)
            if mgr and hasattr(mgr, 'sync_to_cs'):
                mgr.sync_to_cs()

        #log.debug('GSCharacter: cid:', self.cid)
        #cs_call( 'cs_sync_character_data', (self.cid, self.base_att) )
        #self.base_att.syncToCS()
        #self.fellow_mgr.syncFellowToCS()
        #self.bag_equip_mgr.sync_to_cs()

    def load(self, load_data, flag=False):
        ''' 
        @param: flag-离线登陆的标志位 True:离线登陆 False:正常登陆
        '''
        self.base_att.updateGSAttribute( False,  **load_data)
        # 离线登陆时不更新玩家的登陆时间
        if not flag:
            self.base_att.last_login_time = int(time())

    @property
    @defer.inlineCallbacks
    def constellation(self):
        if self.constellation_mgr is None:
            self.constellation_mgr = yield Constellation.load( self.cid )

        defer.returnValue( self.constellation_mgr )

    @staticmethod
    def update(dataset):
        return dict(zip(GSCharacter._fields, dataset))
        #return dict(zip(TABLE_FIELDS[GSCharacter._table][0], dataset))

    def get_buyed_item(self):
        ''' 获取道具商店中的限购道具购买记录 '''
        if not hasattr(self, 'item_shop_mgr'):
            self.item_shop_mgr = GSItemShopMgr(self)
        return self.item_shop_mgr.get_record()
 
    @defer.inlineCallbacks
    def buy_item(self, shop_item_id, item_num):
        ''' 在道具商店中购买道具 '''
        if not hasattr(self, 'item_shop_mgr'):
            self.item_shop_mgr = GSItemShopMgr(self)
        res_err = yield self.item_shop_mgr.buy_item( shop_item_id, item_num )
        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def get_excite_activity_info(self):
        ''' 获取精彩活动的活动列表 '''
        if not hasattr(self, 'excite_activity_mgr'):
            self.excite_activity_mgr = GSExciteActivityMgr(self)
        res_err = yield self.excite_activity_mgr.activity_info()
        defer.returnValue( res_err )
 
    @defer.inlineCallbacks
    def decompose(self, decomposition_type, user_ids):
        ''' 炼化装备、宝物、伙伴 '''
        if not hasattr(self, 'decomposition_mgr'):
            self.decomposition_mgr = GSDecompositionMgr(self)
        res_err = yield self.decomposition_mgr.decomposition( decomposition_type, user_ids )
        defer.returnValue( res_err )
 
    @defer.inlineCallbacks
    def batch_decompose(self, credits):
        ''' 一键转化伙伴 '''
        if not hasattr(self, 'decomposition_mgr'):
            self.decomposition_mgr = GSDecompositionMgr(self)
        res_err = yield self.decomposition_mgr.batch_decompose( credits )
        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def reborn(self, reborn_type, user_id):
        ''' 重生装备、宝物、伙伴 '''
        if not hasattr(self, 'reborn_mgr'):
            self.reborn_mgr = GSRebornMgr( self )
        res_err = yield self.reborn_mgr.reborn( reborn_type, user_id )
        defer.returnValue( res_err )

    #@defer.inlineCallbacks
    #def sync_camp_to_redis(self, update=False):
    #    _all_camps = None
    #    # 是竞技场排行榜中的玩家 则保存其阵容信息
    #    cid_rank_data = yield redis.zscore( SET_ARENA_CID_RANK, self.cid )
    #    if cid_rank_data:
    #        _exists = yield redis.hexists( HASH_CHARACTER_CAMP, self.cid )
    #        if update or (not _exists):
    #            _all_camps = yield self.get_camp()
    #            if _all_camps:
    #                yield redis.hset( HASH_CHARACTER_CAMP, self.cid, dumps(_all_camps) )
    #    else:
    #        _exists = yield redis.hexists( HASH_CHARACTER_CAMP, self.cid )
    #        if _exists:
    #            # 被移出排行榜的玩家, 阵容不保存
    #            yield redis.hdel( HASH_CHARACTER_CAMP, self.cid )

    #    # 夺宝中可被抢夺玩家的阵容更新
    #    _exists = yield redis.hexists( HASH_TREASURE_CHARACTER_CAMP, self.cid )
    #    if _exists:
    #        if not _all_camps:
    #            _all_camps = yield self.get_camp()
    #        if _all_camps:
    #            yield redis.hset( HASH_TREASURE_CHARACTER_CAMP, self.cid, dumps(_all_camps) )

    @property
    def base_att_value(self):
        v = self.base_att.value
        #v['register_time']  = datetime2time( v['register_time'] )
        _steps = []
        try:
            if v['tutorial_steps']:
                _steps = loads( v['tutorial_steps'] )
        except:
            log.exception('unknown tutorial steps value:{0}'.format(v['tutorial_steps']))

        v['tutorial_steps'] =  _steps
        v['friends'] = loads( v['friends'] ) if v['friends'] else []
        v['charge_ids'] = loads( v['charge_ids'] ) if v['charge_ids'] else []
        return v

    def friend_info(self):
        return [self.cid, self.base_att.lead_id, self.base_att.nick_name, self.base_att.level, self.base_att.might]

    @property
    def lead_id(self):
        return self.base_att.lead_id

    @property
    def nick_name(self):
        return self.base_att.nick_name

    @property
    def level(self):
        return self.base_att.level

    @property
    def vip_level(self):
        return self.base_att.vip_level

    @property
    def credits(self):
        return self.base_att.credits

    @property
    def golds(self):
        return self.base_att.golds

    @property
    def account(self):
        return self.base_att.account

    @property
    def friends(self):
        return loads( self.base_att.friends ) if self.base_att.friends else []

    @property
    def charge_ids(self):
        return loads( self.base_att.charge_ids ) if self.base_att.charge_ids else []

    @property
    def douzhan(self):
        return self.base_att.douzhan
    
    @property
    def honor(self):
        return self.base_att.honor

    @property
    def monthly_card(self):
        return self.base_att.monthly_card

    @property
    def dual_monthly_card(self):
        return self.base_att.dual_monthly_card

    def add_douzhan(self, value):
        self.base_att.douzhan += value

    @property
    def might(self):
        return self.base_att.might

    @defer.inlineCallbacks
    def update_might(self, new_might):
        self.base_att.might = new_might
        ms_send('sync_char_data', (self.cid, SYNC_MIGHT, new_might))
        alli_send('sync_char_data', (self.cid, SYNC_MIGHT, new_might))
        #开服狂欢
        yield self.open_server_mgr.update_open_server_activity_quest(OPEN_SERVER_QUEST_ID_14, new_might)
        #成就
        yield self.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_14, new_might)


    def add_friends(self, target_cid):
        ''' 更新玩家的好友列表 '''
        friends = self.friends
        if target_cid not in friends:
            friends.append(target_cid)
            self.base_att.friends = dumps( friends )

    def del_friends(self, target_cid):
        friends = self.friends
        if target_cid in friends:
            friends.remove( target_cid )
            self.base_att.friends = dumps( friends )

    @defer.inlineCallbacks
    def get_finished_group(self):
        yield self.load_dialogue_group()
        defer.returnValue( self.__finished_group )

    @defer.inlineCallbacks
    def load_dialogue_group(self):
        ''' 加载已完成的对话组 '''
        if self.__finished_group is None:
            _data = yield redis.hget(HASH_FINISHED_DIALOGUE_GROUP, self.cid)
            if _data:
                self.__finished_group = loads(_data)
            else:
                self.__finished_group = []
 
    def getCharacterId(self):
        return self.cid

    def get_fellows_limit(self):
        ''' 玩家等级限制阵容中的fellow个数 '''
        _limit_num = 1
        for _idx, _lvl in enumerate(FELLOWS_LIMIT_WITH_PLAYER_LEVEL):
            if self.base_att.level >= _lvl:
                _limit_num = _idx + 1
            else:
                break
        return _limit_num

    def get_golds(self, count, add_type):
        ''' 获得金币记录 '''
        if count <= 0:
            return NO_ERROR
        self.base_att.golds += count
        syslogger(LOG_GOLD_GET, self.cid, self.base_att.level, self.base_att.vip_level, \
                self.alliance_id, count, self.base_att.golds, add_type, '')
        return NO_ERROR

    def consume_golds(self, cost, cost_type):
        ''' 金币数变更记录 '''
        if cost <= 0:
            return NO_ERROR
        if cost > self.base_att.golds:
            return CHAR_GOLD_NOT_ENOUGH
        self.base_att.golds -= cost
        syslogger(LOG_GOLD_LOSE, self.cid, self.base_att.level, self.base_att.vip_level, \
                self.alliance_id, cost, self.base_att.golds, cost_type, '')
        return NO_ERROR

    def get_credits(self, count, add_type):
        ''' 获得钻石记录 '''
        if count <= 0:
            return NO_ERROR
        self.base_att.credits += count
        syslogger(LOG_CREDITS_GET, self.cid, self.base_att.level, self.base_att.vip_level, \
                self.alliance_id, count, self.base_att.credits, add_type, '')
        return NO_ERROR

    @defer.inlineCallbacks
    def consume_credits(self, cost, cost_type):
        ''' 钻石数变更记录 '''
        if cost <= 0:
            defer.returnValue( NO_ERROR )
        if cost > self.base_att.credits:
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        self.base_att.credits -= cost
        # 累计消费活动
        yield self.join_consume_activity(cost)

        syslogger(LOG_CREDITS_LOSE, self.cid, self.base_att.level, self.base_att.vip_level, \
                self.alliance_id, cost, self.base_att.credits, cost_type, '')
        defer.returnValue( NO_ERROR )

    def get_prestige(self, count, add_type):
        ''' 获得声望 '''
        if count <= 0:
            return NO_ERROR
        self.base_att.prestige += count
        syslogger(LOG_PRESTIGE_GET, self.cid, self.base_att.level, self.base_att.vip_level, \
                self.alliance_id, count, self.base_att.prestige, add_type)
        return NO_ERROR

    def consume_prestige(self, cost, cost_type):
        ''' 使用声望 '''
        if cost <= 0:
            return NO_ERROR
        if cost > self.base_att.prestige:
            return CHAR_PRESTIGE_NOT_ENOUGH
        self.base_att.prestige -= cost

        syslogger(LOG_PRESTIGE_LOSE, self.cid, self.base_att.level, self.base_att.vip_level, \
                self.alliance_id, cost, self.base_att.prestige, cost_type)
        return NO_ERROR

    @defer.inlineCallbacks
    def check_eat_peach_status(self, dt_now):
        ''' 检查dt_now时间点是否可吃桃 '''
        # status: 0-不可吃桃, 1-可吃桃
        status, energy, dt_end = 0, 0, 0

        last_end_time = yield redis.hget(HASH_EAT_PEACH, self.cid)
        if last_end_time:
            # 判断当前时间点是否已吃桃
            last_dt = datetime.fromtimestamp( int(last_end_time) )
            if dt_now < last_dt:
                log.warn('Peach had eaten. cid: {0}, last_dt: {1}.'.format( self.cid, last_dt ))
                defer.returnValue( (status, energy, dt_end, [[]]) )

        # 判断时间点是否可吃桃、是否已吃了桃
        conf = get_eat_peach_conf()
        _add_item = []
        for _id, _value in conf.iteritems():
            if _value['StartTime'].time() <= _value['EndTime'].time():
                if dt_now.time() >= _value['StartTime'].time() and dt_now.time() <= _value['EndTime'].time():
                    status = 1
                    energy = _value['AddEnergy']
                    dt_end = _value['EndTime']
                    _add_item = [_value['Rate'], _value['ItemType'], _value['ItemID'], _value['ItemNum']]
                    break
            else:
                if dt_now.time() >= _value['StartTime'].time() or dt_now.time() <= _value['EndTime'].time():
                    status = 1
                    energy = _value['AddEnergy']
                    dt_end = _value['EndTime']
                    _add_item = [_value['Rate'], _value['ItemType'], _value['ItemID'], _value['ItemNum']]
                    break
        if not energy or not dt_end:
            #log.debug('Current time no peach to eat. cid: {0}, conf: {1}.'.format( self.cid, conf ))
            defer.returnValue( (status, energy, dt_end, _add_item) )

        defer.returnValue( (status, energy, dt_end, _add_item) )

    @defer.inlineCallbacks
    def eat_peach(self):
        ''' 吃桃加精力 
        @param peach_data=last_end_time
            last_end_time-上次吃桃后的有效截止时间, peach_id-某一时间段ID
        '''
        dt_now   = datetime.now()
        status, energy, dt_end, _add_item = yield self.check_eat_peach_status(dt_now)
        if not status:
            defer.returnValue( EAT_PEACH_ERROR )
        # 更新吃桃的有效截止时间
        last_dt       = dt_end.replace(dt_now.year, dt_now.month, dt_now.day)
        last_end_time = datetime2time( last_dt )
        yield redis.hset(HASH_EAT_PEACH, self.cid, last_end_time)

        # 每日任务计数
        yield self.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_12, 1 )
        self.base_att.energy += energy
        # 随机奖励
        _stream = yield redis.hget(HASH_EAT_PEACH_REWARD, self.cid)
        if _stream:
            status, times = loads(_stream)
            if status == 1 and timestamp_is_today(times):
                defer.returnValue( (NO_ERROR, self.base_att.energy, [[]]) )
        d = [0, time()]
        yield redis.hset(HASH_EAT_PEACH_REWARD, self.cid, dumps(d)) #当日是否随出过奖励，随出的时间
        r = randint(0, 10000)
        _item_list = []
        _rate, _type, _id, _num = _add_item
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
            defer.returnValue( (NO_ERROR, self.base_att.energy, [_item_list]) )
        if r <= _rate:
            res_err, value = yield model(self, ItemID=_id, ItemNum=_num, AddType=WAY_EAT_PEACH, CapacityFlag=False)
            d = [1, time()]
            yield redis.hset(HASH_EAT_PEACH_REWARD, self.cid, dumps(d))
            _item_list = value[0]

        defer.returnValue( (NO_ERROR, self.base_att.energy, [_item_list]) )

    @defer.inlineCallbacks
    def new_check_monthly_card_status(self, card_type):
        ''' 新增双月卡后 检查月卡的领奖状态 
        @return [left_days, status, prev_status]
        其中 left_days:剩余可领天数; status:今日领奖状态; prev_status:昨日领奖状态;
        '''
        if card_type == MONTHLY_CARD_NORMAL:
            redis_key = HASH_MONTHLY_CARD
            left_days = self.base_att.monthly_card
        elif card_type == MONTHLY_CARD_DUAL:
            redis_key = HASH_DUAL_MONTHLY_CARD
            left_days = self.base_att.dual_monthly_card
        else:
            log.error('cid:{0}, card_type:{1}.'.format( self.cid, card_type ))
            defer.returnValue( [0, 0, 0] )

        status   = 0
        dt_now   = datetime.now()
        old_data = yield redis.hget(redis_key, self.cid)
        # 未购买月卡
        if not old_data:
            # 异常情况
            if left_days > 0:
                status   = 1
                last_dt  = dt_now + timedelta(days=-1)
                old_data = [datetime2time(last_dt), 0]
                yield redis.hset(redis_key, self.cid, dumps(old_data))
            defer.returnValue( [left_days, status, 0] )

        old_data    = loads(old_data)
        last_dt     = datetime.fromtimestamp( old_data[0] )
        delta_days  = (dt_now.date() - last_dt.date()).days
        update_flag = False # update redis flag
        prev_flag   = 0 # 可补领的标志位
        if old_data[1]:
            prev_dt = datetime.fromtimestamp( old_data[1] )
            if 1 == (dt_now.date() - prev_dt.date()).days:
                prev_flag = 1
            else:
                update_flag = True
                old_data[1] = 0

        if delta_days < 1: # 今日已领取
            pass
        elif delta_days == 1: # 昨日已领取
            if left_days > 0:
                status  = 1
        elif (delta_days - left_days) <= 1: # 还有剩余月卡天数
            if delta_days <= left_days:
                status = 1

            if delta_days > 1:
                update_flag = True
                dt_null     = last_dt + timedelta(days=delta_days-1)
                old_data    = [datetime2time(dt_null)]*2
                left_days  -= (delta_days-1)
                prev_flag   = 1
        else: # 月卡天数已用完
            update_flag = False
            status, left_days, old_data[1] = 0, 0, 0
            yield redis.hdel(redis_key, self.cid)

        if update_flag:
            yield redis.hset(redis_key, self.cid, dumps(old_data))

        left_days = left_days if left_days > 0 else 0
        if card_type == MONTHLY_CARD_NORMAL and self.monthly_card != left_days:
            self.base_att.monthly_card = left_days
        elif card_type == MONTHLY_CARD_DUAL and self.dual_monthly_card != left_days:
            self.base_att.dual_monthly_card = left_days
 
        defer.returnValue( [left_days, status, prev_flag] )

    @defer.inlineCallbacks
    def new_monthly_card_reward(self, card_type, day_type):
        if card_type == MONTHLY_CARD_NORMAL:
            redis_key = HASH_MONTHLY_CARD
            limit_id  = LIMIT_ID_MONTHLY_CARD
            left_days = self.base_att.monthly_card
        elif card_type == MONTHLY_CARD_DUAL:
            redis_key = HASH_DUAL_MONTHLY_CARD
            limit_id  = LIMIT_ID_DUAL_MONTHLY_CARD
            left_days = self.base_att.dual_monthly_card
        else:
            defer.returnValue( NO_MONTHLY_CARD_REWARD_ERROR )

        reward_data = yield self.new_check_monthly_card_status(card_type)
        if not reward_data[day_type]:
            log.error('cid:{0}, day_type:{1}, reward_data:{2}.'.format( self.cid, day_type, reward_data ))
            defer.returnValue( NO_MONTHLY_CARD_REWARD_ERROR )
        # 判断前提条件
        back_credits = 0
        if day_type == MONTHLY_CARD_PREV:
            back_credits = get_game_limit_value(limit_id)
        elif day_type == MONTHLY_CARD_TODAY:
            if reward_data[0] < 1:
                log.error("Have no monthly card. cid:{0}, card_type:{1}, day_type:{2}, reward_data:{3}.".format( \
                        self.cid, card_type, day_type, reward_data ))
                defer.returnValue( MONTHLY_CARD_REWARD_ERROR )

            back_credits = get_monthly_card_conf(card_type)
            if not back_credits:
                log.error('No monthly card conf. cid: {0}.'.format( self.cid ))
                defer.returnValue( MONTHLY_CARD_REWARD_ERROR )
        else:
            defer.returnValue( NO_MONTHLY_CARD_REWARD_ERROR )

        card_data = yield redis.hget(redis_key, self.cid)
        if card_data:
            card_data = loads(card_data)
        else:
            card_data = [0, 0]
        # 扣天数 或 修改可追回状态
        if day_type == MONTHLY_CARD_TODAY:
            card_data[0] = int(time())
            left_days   -= 1
            if card_type == MONTHLY_CARD_NORMAL:
                self.base_att.monthly_card = left_days
            elif card_type == MONTHLY_CARD_DUAL:
                self.base_att.dual_monthly_card = left_days
        elif day_type == MONTHLY_CARD_PREV:
            card_data[1] = 0
        else:
            defer.returnValue( MONTHLY_CARD_REWARD_ERROR )

        # 如果已领完, 删除领奖时间
        if left_days < 1 and not card_data[1]:
            yield redis.hdel(redis_key, self.cid)
        else:
            yield redis.hset(redis_key, self.cid, dumps(card_data))

        self.base_att.credits += back_credits

        _status = yield self.new_check_monthly_card_status(MONTHLY_CARD_NORMAL)
        _dual_status = yield self.new_check_monthly_card_status(MONTHLY_CARD_DUAL)
        defer.returnValue( (left_days, self.credits, _status[1], _status[2], _dual_status[1], _dual_status[2]) )

    @defer.inlineCallbacks
    def buy_growth_plan(self):
        ''' 购买成长计划 '''
        # 是否已购买
        if self.base_att.growth_plan > 0:
            log.error("User had buy growth_plan.")
            defer.returnValue( GROWTH_PLAN_BUYED )
        if self.base_att.vip_level < 2:
            log.error("User's vip level less than 2. cid: {0}, vip_level: {1}.".format( self.cid, self.base_att.vip_level ))
            defer.returnValue( GROWTH_PLAN_BUY_LIMIT )
        if self.base_att.credits < GROWTH_PLAN_PRICE:
            log.error('User need more credits. cid: {0}, cur_credits: {1}.'.format( self.cid, self.base_att.credits ))
            defer.returnValue( CHAR_GOLD_NOT_ENOUGH )

        yield self.consume_credits( GROWTH_PLAN_PRICE, WAY_GROWTH_PLAN )
        self.base_att.growth_plan = 1
        _s = yield redis.hget(HASH_BUY_GROW_PLAN_TOTAL_NUM, "buy_grow_total_num")
        _total, _n= loads(_s)
        _total += 1
        yield redis.hset(HASH_BUY_GROW_PLAN_TOTAL_NUM, "buy_grow_total_num", dumps([_total, _n]))
        _, _, status = yield self.growth_plan_status()
        #print self.growth_plan_status()
        defer.returnValue( (self.base_att.credits, _total, status) )

    def check_excite_activity_status(self, activity_id):
        ''' 
        @param: _status-活动状态0:未开启, 1:已开启
        '''
        _status = 0
        _dt_now = datetime.now()
        _conf   = get_excite_activity_conf()
        for _c in _conf.itervalues():
            if _c['ActivityID'] != activity_id:
                continue
            if _c['OpenTime'] > _dt_now or _c['CloseTime'] <= _dt_now:
                _status = 0
            else:
                _status = 1
            break

        return _status

    @defer.inlineCallbacks
    def join_pay_credits_back(self, orderno, charge_id, credits_back):
        ''' 参加充值返还钻石的活动 '''
        if credits_back <= 0:
            defer.returnValue( NO_ERROR )

        _status = self.check_excite_activity_status( EXCITE_PAY_CREDITS_BACK )
        if not _status:
            defer.returnValue( NO_ERROR )
        # 更新已返还的钻石数
        _had_back = yield self.pay_credits_back_status()
        if _had_back >= PAY_CREDITS_BACK_MAX:
            defer.returnValue( NO_ERROR )

        if (_had_back + credits_back) > PAY_CREDITS_BACK_MAX:
            credits_back = PAY_CREDITS_BACK_MAX - _had_back
            _had_back = PAY_CREDITS_BACK_MAX
        else:
            _had_back += credits_back
        yield redis.hset( HASH_PAY_CREDITS_BACK, self.cid, _had_back )
        # 返还的钻石进领奖中心
        yield g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_PAY_CREDITS_BACK, [int(time()), [[ITEM_TYPE_MONEY, ITEM_MONEY_CREDITS, credits_back]]] )
        # add syslog
        syslogger(LOG_PAY_CREDITS_BACK, self.cid, self.level, self.vip_level, self.alliance_id, orderno, charge_id, credits_back)

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def pay_credits_back_status(self):
        ''' 充值返还钻石的详情 '''
        _data = yield redis.hget(HASH_PAY_CREDITS_BACK, self.cid)
        _data = int(_data) if _data else 0

        defer.returnValue( _data )

    @defer.inlineCallbacks
    def join_pay_activity(self, pay_count):
        ''' 参加累计充值的活动 '''
        if pay_count <= 0:
            defer.returnValue( NO_ERROR )

        _status = self.check_excite_activity_status( EXCITE_PAY_ACTIVITY )
        if _status:
            d, _ = yield self.pay_activity_status()
            _had_award_ids, _total_pay = d
            _total_pay += pay_count
            yield redis.hset( HASH_PAY_ACTIVITY, self.cid, dumps([_had_award_ids, _total_pay]) )
        #else:
        #    yield redis.delete(HASH_PAY_ACTIVITY, [] )
        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def pay_activity_status(self):
        ''' 累计充值的详情 '''
        _data = yield redis.hget(HASH_PAY_ACTIVITY, self.cid)
        if _data:
            _data = loads( _data )
        else:
            _data = [[], 0]
        _conf = get_pay_activity_conf()
        item = []
        if _conf:
            for value in _conf.values():
                item.append([value['ID'],value['TotalPay'], value['AwardList']])
        defer.returnValue( [_data, item] )

    @defer.inlineCallbacks
    def check_pay_activity_status(self):
        ''' 返回领奖状态 0-无奖励可领 1-有奖励可领 '''
        _status = 0
        d, _ = yield self.pay_activity_status()
        _had_award_ids, _total_pay = d
        if _total_pay == 0:
            defer.returnValue( (_status, _total_pay) )

        _award_conf = get_pay_activity_conf()
        if not _award_conf:
            defer.returnValue( (_status, _total_pay) )
        for _award in _award_conf.itervalues():
            if _award['ID'] in _had_award_ids:
                continue
            if _award['TotalPay'] <= _total_pay:
                _status = 1
                break

        defer.returnValue( (_status, _total_pay) )

    @defer.inlineCallbacks
    def pay_activity_award(self, award_id):
        ''' 领取累计充值档位奖励 '''
        _status = self.check_excite_activity_status( EXCITE_PAY_ACTIVITY )
        if not _status:
            defer.returnValue( AWARD_HAD_IN_AWARD_CENTER )
        d, _ = yield self.pay_activity_status()
        _had_award_ids, _total_pay = d
        # 已领奖
        if award_id in _had_award_ids:
            log.debug('The award had got. award_id: {0}, _total_pay: {1}.'.format( award_id, _total_pay ))
            defer.returnValue( REPEAT_REWARD_ERROR )
        # 缺少配置
        _award = get_pay_activity_award_conf( award_id )
        _items_list = _award.get('AwardList', [])
        if not _items_list:
            defer.returnValue( NOT_FOUND_CONF )
        # 条件不满足
        if _award['TotalPay'] > _total_pay:
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 道具进背包
        items_return = []
        for _type, _id, _num in _items_list:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                continue
            res_err, value = yield model(self, ItemID=_id, ItemNum=_num, AddType=WAY_PAY_ACTIVITY, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    items_return = total_new_items( _v, items_return )
        # 更新已领记录
        _had_award_ids.append( award_id )
        yield redis.hset( HASH_PAY_ACTIVITY, self.cid, dumps([_had_award_ids, _total_pay]) )
 
        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def join_consume_activity(self, credits):
        _status = self.check_excite_activity_status( EXCITE_CONSUME_ACTIVITY )
        if _status:
            d, _ = yield self.consume_activity_status()
            _had_award_ids, _total_consume = d
            _total_consume += credits
            yield redis.hset( HASH_CONSUME_ACTIVITY, self.cid, dumps([_had_award_ids, _total_consume]) )
        #else:
        #    yield redis.delete(HASH_CONSUME_ACTIVITY, [] )

    @defer.inlineCallbacks
    def consume_activity_status(self):
        ''' 累计消费的详情 '''
        _data = yield redis.hget(HASH_CONSUME_ACTIVITY, self.cid)
        if _data:
            _data = loads( _data )
        else:
            _data = [[], 0]
        
        _conf = get_consume_activity_conf()
        item = []
        if _conf:
            for value in _conf.values():
                item.append([value['ID'], value['TotalConsume'], value['AwardList']])
        defer.returnValue( [_data, item] )

    @defer.inlineCallbacks
    def check_consume_activity_status(self):
        ''' 返回领奖状态 0-无奖励可领 1-有奖励可领 '''
        _status = 0
        d, _ = yield self.consume_activity_status()
        _had_award_ids, _total_consume = d
        if _total_consume == 0:
            defer.returnValue( (_status, _total_consume) )

        _award_conf = get_consume_activity_conf()
        if not _award_conf:
            defer.returnValue( (_status, _total_consume) )
        for _award in _award_conf.itervalues():
            if _award['ID'] in _had_award_ids:
                continue
            if _award['TotalConsume'] <= _total_consume:
                _status = 1
                break

        defer.returnValue( (_status, _total_consume) )

    @defer.inlineCallbacks
    def consume_activity_award(self, award_id):
        ''' 领取累计消费档位奖励 '''
        _status = self.check_excite_activity_status( EXCITE_CONSUME_ACTIVITY )
        if not _status:
            defer.returnValue( AWARD_HAD_IN_AWARD_CENTER )
        d, _ = yield self.consume_activity_status()
        _had_award_ids, _total_consume = d
        # 已领奖
        if award_id in _had_award_ids:
            log.debug('The award had got. award_id: {0}, _total_consume: {1}.'.format( award_id, _total_consume ))
            defer.returnValue( REPEAT_REWARD_ERROR )
        # 缺少配置
        _award = get_consume_activity_award_conf( award_id )
        _items_list = _award.get('AwardList', [])
        if not _items_list:
            defer.returnValue( NOT_FOUND_CONF )
        # 条件不满足
        if _award['TotalConsume'] > _total_consume:
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 道具进背包
        items_return = []
        for _type, _id, _num in _items_list:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                continue
            res_err, value = yield model(self, ItemID=_id, ItemNum=_num, AddType=WAY_CONSUME_ACTIVITY, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    items_return = total_new_items( _v, items_return )
        # 更新已领记录
        _had_award_ids.append( award_id )
        yield redis.hset( HASH_CONSUME_ACTIVITY, self.cid, dumps([_had_award_ids, _total_consume]) )
 
        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def growth_plan_status(self):
        ''' 成长计划的领奖详情 '''
        reward_level = yield redis.hget(HASH_GROWTH_PLAN_REWAED, self.cid)
        if reward_level:
            reward_level = loads( reward_level )
        else:
            reward_level = []
        _s = yield redis.hget(HASH_BUY_GROW_PLAN_TOTAL_NUM, "buy_grow_total_num")
        if not _s:
            _total, _increase_time = 0, time()
        else:
            _total, _increase_time = loads(_s)

        diff = time() - _increase_time
        if _total < 500 and diff > 3600:
            _num = randint(1, 3)
            _total += _num * (diff / 3600)
            _increase_time = time()
        yield redis.hset(HASH_BUY_GROW_PLAN_TOTAL_NUM, "buy_grow_total_num", dumps([_total, _increase_time]))
        _c = sorted(get_grow_server_conf().keys())
        status = []
        got_list = [] # 检查总次数是否能领
        for index, i in enumerate(_c):
            if _total >= i:
                got_list.append(index)

        _stream = yield redis.hget(HASH_BUY_GROW_PLAN_TOTAL_NUM, self.cid)
        if not _stream:
            _data = [0] * len(_c)
            for i in got_list:
                _data[i] = 1
            yield redis.hset(HASH_BUY_GROW_PLAN_TOTAL_NUM, self.cid, dumps(_data))
            for i, j in zip(_c, _data):
                status.append([i, j])
        else:
            _st = loads(_stream)
            for i in got_list:
                if _st[i] == 0:
                    _st[i] = 1
            yield redis.hset(HASH_BUY_GROW_PLAN_TOTAL_NUM, self.cid, dumps(_st))
            for i, j in zip(_c, _st):
                status.append([i, j])
        
        defer.returnValue( [reward_level, _total, status])

    @defer.inlineCallbacks
    def check_growth_plan_status(self):
        ''' 返回领奖状态 0-无奖励可领 1-有奖励可领 2-奖励已领完 '''
        status = 0
        if self.base_att.growth_plan < 1:
            log.debug("User had not buy growth_plan.")
            defer.returnValue( status )

        conf = get_growth_plan_conf()
        if not conf:
            log.error('Not found growth_plan conf. cid: {0}.'.format( self.cid ))
            defer.returnValue( status )

        level_count = 0
        reward_level, _, _ = yield self.growth_plan_status()
        for _lvl in conf.keys():
            if _lvl > self.base_att.level:
                continue
            if _lvl in reward_level:
                level_count += 1
                continue
            status = 1
            break
        #if status !=1:
        #    for i, j in _status:
        #        if j == 1:
        #            status = 1
        #            break

        #if level_count == len(conf.keys()):
        #    status = 2

        defer.returnValue( status )

    @defer.inlineCallbacks
    def growth_plan_reward(self, plan_level):
        ''' 领取成长计划等级奖励 '''
        if self.base_att.growth_plan < 1:
            log.error("User had not buy growth_plan. cid: {0}.".format( self.cid ))
            defer.returnValue( GROWTH_PLAN_REWARD_ERROR )
        # 玩家等级不满足 
        if plan_level > self.base_att.level:
            log.error('User level limit. cid: {0}, cur_level: {1}, plan_level: {2}.'.format( self.cid, self.base_att.level, plan_level ))
            defer.returnValue( CHAR_LEVEL_LIMIT )
        # 已领取奖励
        reward_level, _, _ = yield self.growth_plan_status()
        if plan_level in reward_level:
            log.error('The level reward had got. cid: {0}, plan_level: {1}.'.format( self.cid, plan_level ))
            defer.returnValue( REPEAT_REWARD_ERROR )
        # 缺少配置
        conf      = get_growth_plan_conf()
        plan_conf = conf.get(plan_level, {})
        if not plan_conf:
            log.error('Not found growth_plan conf. cid: {0}, plan_level: {1}.'.format( self.cid, plan_level ))
            defer.returnValue( NOT_FOUND_CONF )

        reward_level.append( plan_level )
        yield redis.hset(HASH_GROWTH_PLAN_REWAED, self.cid, dumps(reward_level))
        # 给奖励
        self.get_credits( plan_conf['CreditsNum'], WAY_GROWTH_PLAN )

        defer.returnValue( (plan_level, self.base_att.credits) )

    @defer.inlineCallbacks
    def get_grow_plan_server_reward(self, buy_num):
        _stream = yield redis.hget(HASH_BUY_GROW_PLAN_TOTAL_NUM, self.cid)
        if _stream:
            status = loads(_stream)
            _c = sorted(get_grow_server_conf().keys())
            _index = _c.index(buy_num)
            _s = yield redis.hget(HASH_BUY_GROW_PLAN_TOTAL_NUM, "buy_grow_total_num")
            total, _ = loads(_s)
            if total >= buy_num and status[_index] == 1:
                _conf = get_grow_server_reward_conf(buy_num)
                if not _conf:
                    log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                    defer.returnValue(UNKNOWN_ITEM_ERROR)
                _type, _id, _num = _conf["RewardList"].split(":")
                model = ITEM_MODELs.get( int(_type), None )
                if not model:
                    log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
                    defer.returnValue(UNKNOWN_ITEM_ERROR)
                res_err, value = yield model(self, ItemID= int(_id), ItemNum= int(_num), AddType=WAY_GROWTH_PLAN_WELFARE, CapacityFlag=False)
                status[_index] = 2
                yield redis.hset(HASH_BUY_GROW_PLAN_TOTAL_NUM, self.cid, dumps(status))
                defer.returnValue([2, value[0]])
        defer.returnValue(GROW_PLAN_GOT)

    @defer.inlineCallbacks
    def check_refresh_status(self):
        _stream = yield redis.hget(HASH_VIP_WELFARE_TIME, self.cid)
        current_refresh_time = get_next_timestamp(6, 23, 59)
        if not _stream:
            yield redis.hset(HASH_VIP_WELFARE_TIME, self.cid, 0)
            _all_conf = get_vip_welfare_conf()
            res = []
            for _conf in _all_conf.itervalues():
                res.append(_conf['Count'])
            yield redis.hset(HASH_VIP_WELFARE_REWARD, self.cid, dumps(res))
            yield redis.hset(HASH_VIP_WELFARE_TIME, self.cid, current_refresh_time)
        else:
            if  _stream < current_refresh_time and _stream != 0:
                _all_conf = get_vip_welfare_conf()
                res = []
                for _conf in _all_conf.itervalues():
                    res.append(_conf['Count'])
                yield redis.hset(HASH_VIP_WELFARE_REWARD, self.cid, dumps(res))
                yield redis.hset(HASH_VIP_WELFARE_TIME, self.cid, current_refresh_time)
            else:
                _streams = yield redis.hget(HASH_VIP_WELFARE_REWARD, self.cid)
                res = loads(_streams)

        defer.returnValue( res )
                
    @defer.inlineCallbacks
    def vip_welfare_status(self):
        _res = yield self.check_refresh_status()
        next_refresh_seconds = get_next_timestamp(6, 23, 59) - time()
        defer.returnValue([next_refresh_seconds, _res])

    @defer.inlineCallbacks
    def vip_welfare_reward(self, t_type):
        ''' 购买VIP福利 '''
       
        if self.vip_level < t_type:
            defer.returnValue(CHAR_VIP_LEVEL_LIMIT)
        
        _stream = yield redis.hget(HASH_VIP_WELFARE_REWARD, self.cid)
        if _stream:
            _data = loads(_stream)
            buy_count = _data[t_type]
            if buy_count <= 0:
                defer.returnValue(BUY_MAX_NUM_ERROR)
        else:
            defer.returnValue(BUY_MAX_NUM_ERROR)
        # 道具进背包
        _conf = get_vip_welfare_conf(t_type)
        if _conf is None:
            defer.returnValue(UNKNOWN_ITEM_ERROR)
        _type, _id, _num = _conf['ItemType'], _conf['ItemID'], _conf['ItemNum']
        model = ITEM_MODELs.get( _type, None )
        if not model:
            log.error('Unknown item type. item info: {0}.'.format( (_type, _id, _num) ))
            defer.returnValue(UNKNOWN_ITEM_ERROR)
        if self.credits < _conf["PresentPrice"]:
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        res_err, value = yield model(self, ItemID=_id, ItemNum=_num, AddType=WAY_VIP_WELFARE, CapacityFlag=False, CostCredits=_conf['PresentPrice'])
        _data[t_type] = buy_count - 1
        yield redis.hset(HASH_VIP_WELFARE_REWARD, self.cid, dumps(_data))
        _res = [value[0], buy_count-1, self.credits] 
        defer.returnValue( _res )

    @defer.inlineCallbacks
    def get_lucky_turntable_info(self):
        ''' get old lucky turntable info '''
        turntable_info = yield redis.hget(HASH_LUCKY_TURNTABLE, self.cid)
        if turntable_info:
            turntable_info = loads( turntable_info )
        else:
            turntable_info = {}

        defer.returnValue( turntable_info )

    @defer.inlineCallbacks
    def lucky_turntable_status(self):
        ''' 幸运转盘的基本信息 '''
        # today total pay
        total_pay = yield get_daily_pay_record(self.cid)
        # check turntable_type
        status = []
        dt_now = datetime.now()
        turntable_info = yield self.get_lucky_turntable_info()
        all_turntable_conf = get_lucky_turntable_conf()
        for _type, _conf in all_turntable_conf.items():
            had_lucky, had_reward = 1, 1
            if total_pay < _conf['TotalPay']:
                had_lucky, had_reward = 0, 0
                status.append( [_type, had_lucky, had_reward] )
                continue
            _info = turntable_info.get(_type, [])
            if not _info:
                status.append( [_type, had_lucky, had_reward] )
                continue
            # check last lucky time
            if _info[0]:
                last_l_dt = datetime.fromtimestamp( int(_info[0]) )
                if dt_now.date() == last_l_dt.date():
                    had_lucky = 0
            # check last reward time
            if _info[1]:
                last_r_dt = datetime.fromtimestamp( int(_info[1]) )
                if dt_now.date() == last_r_dt.date():
                    had_reward = 0
            status.append( [_type, had_lucky, had_reward] )

        defer.returnValue( [total_pay, status] )

    @defer.inlineCallbacks
    def turntable_item(self, turntable_type):
        ''' 抽取幸运道具 '''
        turntable_info = yield self.get_lucky_turntable_info()
        _info = turntable_info.get(turntable_type, [])
        _info = _info if _info else [0, 0]
        # check last lucky time
        dt_now = datetime.now()
        if _info[0]:
            last_l_dt = datetime.fromtimestamp( int(_info[0]) )
            if dt_now.date() == last_l_dt.date():
                defer.returnValue( LUCKY_TURNTABLE_REPEAT_ERROR )
        # today total pay
        total_pay = yield get_daily_pay_record(self.cid)
        all_turntable_conf = get_lucky_turntable_conf()
        _conf = all_turntable_conf.get(turntable_type, {})
        if not _conf:
            defer.returnValue( UNKNOWN_TURNTABLE_TYPE_ERROR )
        if total_pay < _conf['TotalPay']:
            defer.returnValue( TURNTABLE_PAY_NOT_ENOUGH )

        chest_id  = TURNTABLE_ITEM_POOLS[turntable_type]
        item_rand = yield package_open(self, chest_id)
        if not item_rand:
            defer.returnValue( NOT_FOUND_CONF )

        _model = ITEM_MODELs.get(item_rand[0], None)
        value  = []
        if _model:
            res_err, value = yield _model(self, ItemID=item_rand[1], ItemNum=item_rand[2], CapacityFlag=False, AddType=WAY_LUCKY_TURNTABLE)
            if not res_err:
                _info[0] = int(time())
                turntable_info[turntable_type] = _info
                yield redis.hset( HASH_LUCKY_TURNTABLE, self.cid, dumps(turntable_info) )
            else:
                defer.returnValue( res_err )
        else:
            log.error('Unknown item type. cid: {0}, ItemType: {1}.'.format( self.cid, _type ))

        defer.returnValue( value )

    @defer.inlineCallbacks
    def turntable_reward(self, turntable_type):
        ''' 领取金币奖励 '''
        turntable_info = yield self.get_lucky_turntable_info()
        _info = turntable_info.get(turntable_type, [])
        _info = _info if _info else [0, 0]
        # check last lucky time
        dt_now = datetime.now()
        if _info[1]:
            last_l_dt = datetime.fromtimestamp( int(_info[1]) )
            if dt_now.date() == last_l_dt.date():
                defer.returnValue( LUCKY_TURNTABLE_REPEAT_ERROR )
        # today total pay
        total_pay = yield get_daily_pay_record(self.cid)
        all_turntable_conf = get_lucky_turntable_conf()
        _conf = all_turntable_conf.get(turntable_type, {})
        if not _conf:
            defer.returnValue( UNKNOWN_TURNTABLE_TYPE_ERROR )
        if total_pay < _conf['TotalPay']:
            defer.returnValue( TURNTABLE_PAY_NOT_ENOUGH )

        self.get_golds( _conf['RewardGolds'], WAY_LUCKY_TURNTABLE )

        _info[1] = int(time())
        turntable_info[turntable_type] = _info
        yield redis.hset( HASH_LUCKY_TURNTABLE, self.cid, dumps(turntable_info) )
        defer.returnValue( [self.golds] )

    @defer.inlineCallbacks
    def update_battle_attr(self, soul=0, gold=0, exp=0, way_type=WAY_SCENE_BATTLE):
        if soul > 0:
            self.base_att.soul  += soul
        if gold > 0:
            #self.base_att.golds += gold
            self.get_golds( gold, WAY_SCENE_BATTLE )
        if exp > 0:
            self.base_att.exp   += exp
            # add syslog
            syslogger(LOG_CHAR_EXP_GET, self.cid, self.base_att.level, self.base_att.vip_level, self.alliance_id, exp, way_type)

        yield self.levelup(self.base_att.level, self.base_att.exp)

    def expand_bag(self, bag_type, bag_count):
        ''' 背包扩充 '''
        if BAG_TYPE_CAPACITY[bag_type] == 'equip_capacity':
            self.base_att.equip_capacity      = bag_count
        elif BAG_TYPE_CAPACITY[bag_type] == 'equipshard_capacity':
            self.base_att.equipshard_capacity = bag_count
        elif BAG_TYPE_CAPACITY[bag_type] == 'fellow_capacity':
            self.base_att.fellow_capacity     = bag_count
        elif BAG_TYPE_CAPACITY[bag_type] == 'fellowsoul_capacity':
            self.base_att.fellowsoul_capacity = bag_count
        elif BAG_TYPE_CAPACITY[bag_type] == 'item_capacity':
            self.base_att.item_capacity       = bag_count
        elif BAG_TYPE_CAPACITY[bag_type] == 'treasure_capacity':
            self.base_att.treasure_capacity   = bag_count
        else:
            log.error('Unknown bag type.')

    @defer.inlineCallbacks        
    def levelup(self, cur_level, cur_exp):
        '''玩家升级
        '''
        _max_level = get_max_role_level()
        while cur_exp > 0:
            _roleexp_conf = get_roleexp_by_level( cur_level )
            _need_exp     = _roleexp_conf.get( FELLOW_QUALITY[-1], 0 )
            if not _need_exp:
                log.error("Can not find the roleexp's conf. cur_level: {0}.".format( cur_level ))
                break
            # 升级所需经验不足
            if cur_exp < _need_exp:
                break
            # 已升级到最高等级
            if cur_level >= _max_level:
                break
            cur_exp -= _need_exp
            cur_level += 1

        cur_level = cur_level if cur_level <= _max_level else _max_level
        if cur_level > self.base_att.level:
            self.base_att.level = cur_level
            syslogger(LOG_LEVELUP, self.cid, self.cid, cur_level, self.vip_level)
            ms_send('sync_char_data', (self.cid, SYNC_LEVEL, cur_level))
            alli_send('sync_char_data', (self.cid, SYNC_LEVEL, cur_level))
            # 同步camp到redis
            #yield self.sync_camp_to_redis(update=True)

        self.base_att.exp = cur_exp
        # 开服七天
        yield self.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_4, cur_level)
        #成就
        yield self.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_4, cur_level)

    @defer.inlineCallbacks
    def get_camp(self, flag=False):
        '''
        @summary: 获取玩家的阵容信息, flag=True 离线登陆的标志位
        @return : _all_camps format: 
            [max_camp_fellows, [[camp_id, [fellow], [helmet]], ...]]
        '''
        # 阵容中已解锁的小伙伴个数 和玩家等级相关
        yield self.fellow_mgr.value_list
        _limit_num   = self.get_fellows_limit()
        _all_camps   = [_limit_num, [], [], [], self.base_att.chaos_level, []]
        _camp_fellow = self.fellow_mgr.get_camp_fellow()
        for _idx, _ufid in enumerate( _camp_fellow ):
            if _ufid <= 0:
                _all_camps[1].append( [] )
                continue
            # 获取camp_id上的fellow
            _fellow_obj  = self.fellow_mgr.get_fellow( _ufid )
            if not _fellow_obj:
                _all_camps[1].append( [] )
                log.error('Unknown _ufid. cid: {0}, _ufid: {1}.'.format( self.cid, _ufid ))
                continue
            # 主角fellow 
            if _fellow_obj.is_major > 0:
                _fellow_id  = self.base_att.lead_id
                _fellow_lvl = self.base_att.level
            else:
                _fellow_id  = _fellow_obj.fellow_id
                _fellow_lvl = _fellow_obj.level
            _fellow_data = [_ufid, _fellow_id, _fellow_lvl, _fellow_obj.advanced_level]

            # 获取camp_id上的装备
            _camp_equip    = yield self.bag_equip_mgr.get_camp_equip( _idx + 1 )
            # 获取camp_id上的宝物
            _camp_treasure = yield self.bag_treasure_mgr.get_camp_treasure( _idx + 1 )
            _all_camps[1].append( [_idx+1, _fellow_data, _camp_equip[0], _camp_equip[1], _camp_equip[2], _camp_equip[3], _camp_treasure[0], _camp_treasure[1]] )
            # 获取camp上的玉魄
            _camp_jade    = yield self.bag_jade_mgr.get_camp_jade( _idx + 1 )
            _all_camps[5].append( _camp_jade )

        if (not _all_camps[1]) or (not _all_camps[1][0]): # 缺少主角信息
            log.error("User's fellow data error. cid: {0}, _all_camps: {1}.".format( self.cid, _all_camps ))
            defer.returnValue( None )

        # 获取对手玩家的阵型
        if flag:
            _all_camps[2] = self.fellow_mgr.get_camp_predestine_fid()
            _all_camps[3] = yield self.fellow_mgr.get_offline_formation()
        else:
            _all_camps[2] = self.fellow_mgr.get_camp_predestine()

        defer.returnValue( _all_camps )

    @defer.inlineCallbacks
    def set_camp_one_touch(self, camp_id, one_touch_data):
        '''
        @summary: 一键装备
        '''
        _camp_fellow = self.fellow_mgr.get_camp_fellow()
        if _camp_fellow[camp_id-1] <= 0:
            log.error('No fellow in camp. cid: {0}, camp_id: {1}.'.format( self.cid, camp_id ))
            defer.returnValue( CLIENT_DATA_ERROR )
        res_err = yield self.bag_equip_mgr.set_one_touch(camp_id, one_touch_data[0:4])
        if res_err:
            defer.returnValue( res_err )

        res_err = yield self.bag_treasure_mgr.set_one_touch(camp_id, one_touch_data[4:])
        # 同步camp到redis
        #yield self.sync_camp_to_redis(update=True)

        defer.returnValue( res_err )
    
    @defer.inlineCallbacks
    def set_camp_predestine(self, camp_pos_id, old_ufid, new_ufid):
        '''
        @summary: 设置上阵伙伴的羁绊
        '''
        if camp_pos_id > 6:
            log.error('Unknown camp predestine position id. cid: {0}.'.format( self.cid ))
            defer.returnValue( CLIENT_DATA_ERROR )
        # 判断羁绊位置是否解锁
        if self.base_att.level < FELLOWS_LIMIT_WITH_PLAYER_LEVEL[camp_pos_id + 4]:
            log.error('Camp predestine position id locked. cid: {0}.'.format( self.cid ))
            defer.returnValue( CLIENT_DATA_ERROR )
        res_err = yield self.fellow_mgr.set_camp_predestine( camp_pos_id, old_ufid, new_ufid )
        # 同步camp到redis
        #yield self.sync_camp_to_redis(update=True)

        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def add_credits(self, orderno, charge_id, platform_id, parent_id, currency_type, currency):
        ''' 
        @param : ChargeType 1-充值,2-月卡
        @param : credits_payed 当前VIP Level下 还有的金额数
        '''
        curr_vip_level = self.base_att.vip_level
        conf = get_vip_chargelist_conf( curr_vip_level, charge_id )
        if not conf:
            log.error("Unknown charge_id. cid: {0}, curr_vip_level: {1}, charge_id: {2}.".format( self.cid, curr_vip_level, charge_id ))
            defer.returnValue( (NOT_FOUND_CONF, 0) )
        # 判断限时开始时间和限时时长
        dt_now = datetime.now()
        if conf['StartTime']:
            dt_end = conf['StartTime'] + timedelta( conf['Duration'] )
            if dt_now < conf['StartTime'] or dt_now > dt_end:
                log.error("Valid charge_id. cid: {0}, curr_vip_level: {1}, charge_id: {2}.".format( self.cid, curr_vip_level, charge_id ))
                defer.returnValue( (UNKNOWN_ERROR, conf['ChargeType']) )

        credits = conf['GetCredits'] + conf['GiftCredits']
        self.base_att.total_cost += conf['Cost']
        # 累计充值
        yield self.join_pay_activity( conf['Cost'] )
        # 充值返利
        yield self.join_pay_credits_back( orderno, charge_id, conf['CreditsBack'] )
        # 玩家首充礼包进领奖中心 DK-2075 月卡计入首充
        way_type = WAY_CREDITS_PAYMENT
        #if (conf['ChargeType'] == 1) and (self.base_att.firstpay == 0):
        if (self.base_att.firstpay == 0):
            way_type = WAY_FIRSTPAY
            self.base_att.firstpay = 1
            yield g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_FIRSTPAY, [int(time())] )
        # 充值档位都单独计算首充
        had_charge_ids = self.charge_ids
        if charge_id not in had_charge_ids:
            had_charge_ids.append( charge_id )
            self.base_att.charge_ids = dumps( had_charge_ids )
            credits = conf['GetCredits'] + conf['FirstGiftCredits']
        # 月卡充值
        if conf['ChargeType'] == MONTHLY_CARD_NORMAL:
            way_type = WAY_MONTHLY_CARD
            self.base_att.monthly_card += 30
            # 记录买月卡的起始日, 从此开始每天可领奖励, 未领的奖励放入领奖中心
            card_data = yield redis.hget(HASH_MONTHLY_CARD, self.cid)
            if not card_data:
                dt_buy = dt_now + timedelta(days=-1)
                yield redis.hset(HASH_MONTHLY_CARD, self.cid, dumps([datetime2time(dt_buy), 0]))
        # 双月卡充值
        elif conf['ChargeType'] == MONTHLY_CARD_DUAL:
            way_type = WAY_DUAL_MONTHLY_CARD
            self.base_att.dual_monthly_card += 30
            # 记录买月卡的起始日, 从此开始每天可领奖励, 未领的奖励放入领奖中心
            card_data = yield redis.hget(HASH_DUAL_MONTHLY_CARD, self.cid)
            if not card_data:
                dt_buy = dt_now + timedelta(days=-1)
                yield redis.hset(HASH_DUAL_MONTHLY_CARD, self.cid, dumps([datetime2time(dt_buy), 0]))

        # syslog
        syslogger(LOG_PAYMENT, self.cid, self.cid, self.level, curr_vip_level, orderno, charge_id, conf['Cost'], credits)
        # add credits
        self.get_credits( credits, way_type )
        # credits_payed-当前VIP Level下 还有的金额数
        curr_payed = self.base_att.credits_payed + conf['Cost']
        while curr_payed > 0:
            _vip_conf = get_vip_conf( curr_vip_level + 1 )

            if not _vip_conf:
                log.debug('No next vip conf. level: {0}.'.format( curr_vip_level+1 ))
                break
            else:
                _need_pay = _vip_conf['Cost']
                if curr_payed < _need_pay:
                    log.debug('No enough ren min bi. curr_payed: {0}, _need_pay: {1}.'.format( curr_payed, _need_pay ))
                    break
                else:
                    curr_payed -= _need_pay
                    curr_vip_level += 1

                    yield redis.hset(HASH_VIP_LEVELUP_RECORD % self.cid, curr_vip_level, 1)

        if curr_vip_level > self.vip_level:
            msg = [10, [self.nick_name, self.lead_id, curr_vip_level]]
            gw_broadcast('sync_broadcast', [[3, msg]])

        self.base_att.vip_level     = curr_vip_level
        self.base_att.credits_payed = curr_payed
        ms_send('sync_char_data', (self.cid, SYNC_VIP_LEVEL, curr_vip_level))
        alli_send('sync_char_data', (self.cid, SYNC_VIP_LEVEL, curr_vip_level))
        # update daily pay record
        add_daily_pay_record( self.cid, conf['Cost'] )
        
        # 开服七天
        yield self.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_2, self.base_att.total_cost)
        #成就
        yield self.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_18, self.vip_level)

        msg = [9, [self.nick_name, self.lead_id, charge_id, curr_vip_level]]
        gw_broadcast('sync_broadcast', [[3, msg]])

        defer.returnValue( (NO_ERROR, conf['ChargeType']) )

    @defer.inlineCallbacks
    def set_finished_group(self, scene_id, group_id, dialogue_id):
        ''' 更新已完成的对话组 '''
        yield self.load_dialogue_group()
        if group_id not in self.__finished_group:
            self.__finished_group.append( group_id )
            yield redis.hset( HASH_FINISHED_DIALOGUE_GROUP, self.cid, dumps(self.__finished_group) )
        else:
            log.error('The group id had finished.')

    def update_chaos(self, next_level):
        ''' 升级混沌 '''
        if (next_level - self.base_att.chaos_level) != 1:
            log.error('Next level bigger cur level than 1. cur_level: {0}.'.format( self.base_att.chaos_level ))
            return REQUEST_LIMIT_ERROR
        _conf = get_chaos_conf( next_level )
        if not _conf:
            log.error('Can not find the conf. cid: {0}, level: {1}.'.format( self.cid, next_level ))
            return NOT_FOUND_CONF
        # 判断金币、副本星星数量是否足够
        if _conf['CostGold'] > self.base_att.golds \
                or _conf['CostStarNum'] > self.base_att.scene_star:
            log.error('Char golds or scene star not enough. need golds: {0}, cur golds: {1}, need star: {2}, cur star: {3}.'.format( _conf['CostGold'], self.base_att.golds, _conf['CostStarNum'], self.base_att.scene_star ))
            return REQUEST_LIMIT_ERROR
        # 混沌升级
        #self.base_att.golds      -= _conf['CostGold']
        self.consume_golds( _conf['CostGold'], WAY_CHAOS_UPDATE )
        self.base_att.scene_star -= _conf['CostStarNum']
        syslogger(LOG_SCENESTAR_LOSE, self.cid, self.level, self.vip_level, self.alliance_id, _conf['CostStarNum'], self.base_att.scene_star, next_level)
        self.base_att.chaos_level += 1
        # 判断玩家是否需要变身
        if 0 < _conf['ChangeRole'] and self.lead_id < 11:
            self.base_att.lead_id += 2
            ms_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
            alli_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
        #if _conf['ChangeRole'] == 1:
        #    if self.base_att.lead_id <= 2:
        #        self.base_att.lead_id += 2
        #        ms_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
        #        alli_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
        #elif _conf['ChangeRole'] == 2:
        #    if self.base_att.lead_id <= 4:
        #        self.base_att.lead_id += 2
        #        ms_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
        #        alli_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
        
        return self.base_att.chaos_level, self.base_att.scene_star, _conf['ChangeRole'], self.base_att.lead_id

    def finish_tutorial(self, step):
        _steps_finished = loads( self.base_att.tutorial_steps ) if self.base_att.tutorial_steps else []

        if step in _steps_finished:
            return CHAR_TUTORIAL_FINISHED
        else:
            _steps_finished.append( step )
            self.base_att.tutorial_steps = dumps( _steps_finished )
            syslogger(LOG_TUTORIAL, self.cid, self.cid, self.level, self.vip_level, step)
            return NO_ERROR


    def check_function_open(self, function_id):
        ''' 检查功能开放限制 =0:open, >0:limit. '''
        _func_conf = get_function_open_conf(function_id)
        if not _func_conf:
            return NO_ERROR
        # 检查等级限制
        if self.level < _func_conf['RoleLevel']:
            log.warn('User role level limit. function_id:{0}, cid:{1}, need:{2}, curr:{3}.'.format( function_id, self.cid, _func_conf['RoleLevel'], self.level ))
            return CHAR_LEVEL_LIMIT

        return NO_ERROR

    def update_chaos_auto(self, tar_level):
        '''一键升级混沌 '''
        if tar_level <= self.base_att.chaos_level:
            return REQUEST_LIMIT_ERROR
        _conf = get_auto_chaos_conf( self.base_att.golds, self.base_att.scene_star, self.base_att.chaos_level, tar_level )
        if _conf[0] == 0 and _conf[1] == 0:
            return REQUEST_LIMIT_ERROR
        # 混沌升级
        self.consume_golds( _conf[0], WAY_CHAOS_UPDATE )
        self.base_att.scene_star -= _conf[1]
        self.base_att.chaos_level += _conf[2]
        syslogger(LOG_SCENESTAR_LOSE, self.cid, self.level, self.vip_level, self.alliance_id, _conf[1], self.base_att.scene_star, self.base_att.chaos_level)
        # 判断玩家是否需要变身
        if len(_conf[3]) > 0 and self.lead_id < 11:
            self.base_att.lead_id += 2 * len(_conf[3])
            ms_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
            alli_send('sync_char_data', (self.cid, SYNC_LEAD_ID, self.base_att.lead_id))
        _conf[3].sort()
        role = role[-1] if len(_conf[3]) > 0 else 0
        return self.base_att.chaos_level, self.base_att.scene_star, role, self.base_att.lead_id
