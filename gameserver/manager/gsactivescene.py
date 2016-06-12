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
from marshal  import loads, dumps     
from utils    import datetime2string, string2datetime
from errorno  import *
from constant import *
from redis    import redis
from system   import get_vip_conf, get_activescene_conf, get_drop_conf, get_gold_tree_conf
from syslogger import syslogger

from twisted.internet       import defer
from models.item            import *
from models.characterserver import gs_load_table_data, gs_create_table_data
from manager.gsattribute    import GSAttribute
from table_fields           import TABLE_FIELDS


class GSActiveSceneMgr(object):
    '''
    ( 'id', 'cid', 'panda_free', 'panda_buyed', 'panda_left_buy', 'treasure_free', 'treasure_buyed', 'treasure_left_buy', 'tree_free', 'tree_buyed', 'tree_left_buy', 'last_datetime' )
    '''
    _table = 'activescene'
    _fields = TABLE_FIELDS['activescene'][0]

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        self.load_flag = False

        # 单次战斗中伙伴复活的次数
        self.revive_count = 0
        # 战斗中的活动副本ID
        self.old_activescene_id = 0
        self.activescene = GSAttribute(user.cid, GSActiveSceneMgr._table, user.cid)

    @defer.inlineCallbacks
    def load(self):
        if not self.load_flag:
            try:
                table_data = yield gs_load_table_data(self.cid, GSActiveSceneMgr._table)
                # 注意在收到返回消息后才能赋值
                self.load_flag = True
                #log.info('For Test. table_data: {0}.'.format( table_data ))
                if table_data:
                    table_data = dict(zip(GSActiveSceneMgr._fields, table_data))
                    #log.info('For Test. updateGSAttribute. table_data: {0}.'.format( table_data ))
                    self.activescene.updateGSAttribute( False,  **table_data)
                else:
                    yield self.new()
            except Exception as e:
                log.error( 'Exception raise. e: {0}.'.format( e ))

    def sync_to_cs(self):
        if self.activescene:
            self.activescene.syncToCS()

    @defer.inlineCallbacks
    def new(self):
        now_weekday = datetime.now().isoweekday()

        conf = get_vip_conf( self.user.base_att.vip_level )
        left_buy = conf['ActiveSceneCount'] if conf else 0

        conf = get_activescene_conf( ACTIVE_PANDA_ID )
        panda_free = self.isOpenCycle( conf, now_weekday )

        conf = get_activescene_conf( ACTIVE_TREASURE_ID )
        treasure_free = self.isOpenCycle( conf, now_weekday )

        conf = get_activescene_conf( ACTIVE_TREE_ID )
        tree_free = self.isOpenCycle( conf, now_weekday )

        dt_now = datetime.now()
        init_data = [self.cid, panda_free, 0, left_buy, treasure_free, 0, left_buy, tree_free, 0, left_buy, dt_now]
        kwargs = dict(zip(GSActiveSceneMgr._fields[1:], init_data))
        create_data = yield gs_create_table_data(self.cid, GSActiveSceneMgr._table, **kwargs)
        if create_data:
            create_data = dict(zip(GSActiveSceneMgr._fields, create_data))
            self.activescene.updateGSAttribute( False,  **create_data)
        else: # 新增数据失败
            self.load_flag = False

        defer.returnValue( NO_ERROR )
    
    @property
    def value(self):
        conf  = get_vip_conf( self.user.vip_level )
        total = conf['ActiveSceneCount'] if conf else 0
        panda_left    = total - self.activescene.panda_left_buy if total > self.activescene.panda_left_buy else 0
        treasure_left = total - self.activescene.treasure_left_buy if total > self.activescene.treasure_left_buy else 0
        tree_left     = total - self.activescene.tree_left_buy if total > self.activescene.tree_left_buy else 0
        return ((ACTIVE_PANDA_ID, self.activescene.panda_free+self.activescene.panda_buyed, panda_left), \
                (ACTIVE_TREASURE_ID, self.activescene.treasure_free+self.activescene.treasure_buyed, treasure_left), \
                (ACTIVE_TREE_ID, self.activescene.tree_free+self.activescene.tree_buyed, tree_left))

    @defer.inlineCallbacks
    def system_daily_reset(self):
        '''
        @summary: 每个活动副本有玩家等级限制 和 固定的开启时间: 星期几及时间段
                每天24点系统重置活动副本数据, 含免费挑战次数、剩余可够买的次数、更新时间
        '''
        yield self.load()
        dt_now  = datetime.now()
        dt_last = self.activescene.last_datetime
        if dt_now.date() != dt_last.date():
            now_weekday = dt_now.isoweekday()

            self.activescene.panda_left_buy    = 0
            self.activescene.treasure_left_buy = 0
            self.activescene.tree_left_buy     = 0

            conf = get_activescene_conf( ACTIVE_PANDA_ID )
            self.activescene.panda_free = self.isOpenCycle( conf, now_weekday )

            conf = get_activescene_conf( ACTIVE_TREASURE_ID )
            self.activescene.treasure_free = self.isOpenCycle( conf, now_weekday )

            conf = get_activescene_conf( ACTIVE_TREE_ID )
            self.activescene.tree_free = self.isOpenCycle( conf, now_weekday )

            self.activescene.last_datetime = dt_now

    def isOpenCycle(self, conf, weekday):
        '''
        check OpenCycle return today free count
        '''
        free_num  = 0
        if not conf:
            return free_num

        open_cycle = conf['OpenCycle']
        if open_cycle:
            open_cycle = map( int, open_cycle.split(',') )
            if weekday in open_cycle:
                free_num = conf['CleanNum']
        else:
            free_num = conf['CleanNum']

        return free_num

    @defer.inlineCallbacks
    def activescene_data(self):
        '''
        @summary: 获取精英副本的基本信息
        '''
        yield self.system_daily_reset()
        defer.returnValue( self.value )

    @defer.inlineCallbacks
    def start_battle(self, activescene_id):
        '''
        @summary: 记录玩家的战斗信息
        '''
        conf = get_activescene_conf( activescene_id )
        if not conf:
            log.error('Unknown activescene conf. id: {0}.'.format( activescene_id ))
            defer.returnValue( NOT_FOUND_CONF )

        dt_now  = datetime.now()
        # 检查活动副本是否开启
        if conf['OpenCycle']:
            cycle_list = map(int, conf['OpenCycle'].split(','))
            if dt_now.isoweekday() not in cycle_list:
                log.error('Active not opened. OpenCycle: {0}.'.format( conf['OpenCycle'] ))
                defer.returnValue( ACTIVE_FIGHT_TIME_ERROR )
        if conf['OpenTime']:
            if dt_now.time() < conf['OpenTime'].time():
                log.error('Active not opened. OpenTime: {0}.'.format( conf['OpenTime'] ))
                defer.returnValue( ACTIVE_FIGHT_TIME_ERROR )
        if conf['CloseTime']:
            if dt_now.time() > conf['CloseTime'].time():
                log.error('Active had closed. CloseTime: {0}.'.format( conf['CloseTime'] ))
                defer.returnValue( ACTIVE_FIGHT_TIME_ERROR )
        # 玩家等级限制
        if conf['NeedRoleLevel'] > self.user.base_att.level:
            log.error('User level limit. need: {0}, cur: {1}.'.format( conf['NeedRoleLevel'], self.user.base_att.level ))
            defer.returnValue( CHAR_LEVEL_LIMIT )

        # 每日挑战次数限制
        yield self.system_daily_reset()
        if activescene_id == ACTIVE_PANDA_ID:
            if (self.activescene.panda_free+self.activescene.panda_buyed < 1):
                log.error('No fight count. panda_free: {0}, panda_buyed: {1}.'.format( self.activescene.panda_free, self.activescene.panda_buyed ))
                defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
        elif activescene_id == ACTIVE_TREASURE_ID:
            if (self.activescene.treasure_free+self.activescene.treasure_buyed < 1):
                log.error('No fight count. treasure_free: {0}, treasure_buyed: {1}.'.format( self.activescene.treasure_free, self.activescene.treasure_buyed ))
                defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
        elif activescene_id == ACTIVE_TREE_ID:
            if (self.activescene.tree_free+self.activescene.tree_buyed < 1):
                log.error('No fight count. tree_free: {0}, tree_buyed: {1}.'.format( self.activescene.tree_free, self.activescene.tree_buyed ))
                defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
        else:
            log.error('Unknown activescene_id: {0}.'.format( activescene_id ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        self.revive_count = 0
        self.old_activescene_id = activescene_id

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def dungeon_star_drop(self, dungeon_id, dungeon_star=1):
        '''
        @summary: 精英副本默认难度为1, 无conf则不用计算掉落
        @param  : drop_items-[ [item_type, item_id, item_num], ... ]
        '''
        drop_items=[]

        drop_conf = get_drop_conf( dungeon_id, dungeon_star )
        if not drop_conf:
            log.error('No drop conf. dungeon_id: {0}, dungeon_star: {1}.'.format( dungeon_id, dungeon_star ))
            defer.returnValue( drop_items )

        # old_rate format: {dungeon_star: {drop_id: rate, ...}, ...}
        old_rate  = {}
        data = yield redis.hget( HASH_DUNGEON_DROP_RATE % dungeon_id, self.cid )
        if data:
            old_rate = loads( data )
            if old_rate.has_key( dungeon_star ):
                old_star_rate = old_rate[dungeon_star]
            else:
                old_star_rate = {}
                old_rate[dungeon_star] = old_star_rate
                for _id, _drop in drop_conf.iteritems():
                    old_star_rate[_id] = _drop['RateMax']
        else: # 第一次按照最大概率来计算掉落
            old_star_rate = {}
            old_rate[dungeon_star] = old_star_rate
            for _id, _drop in drop_conf.iteritems():
                old_star_rate[_id] = _drop['RateMax']

        for _drop_id, _drop in drop_conf.iteritems():
            add_rate   = old_star_rate.setdefault(_drop_id, 0)
            _drop_rate = _drop['RateStart'] + add_rate
            # 单次增加的封顶概率
            if _drop_rate > _drop['RateMax']:
                _drop_rate = _drop['RateMax']
            # 掉落概率是万分比
            rand_int = random.randint(0, 10000)
            #log.info('For Test. rand_int: {0}, _drop_rate: {1}, _drop_id: {2}, _drop_num: {3}.'.format( rand_int, _drop_rate, _drop['ItemID'], _drop['ItemNum'] ))
            # _drop['QuestID'] 未处理
            # 当前随机值 不大于 配置的掉落概率值时掉落
            if rand_int <= _drop_rate:
                drop_items = add_new_items( [_drop['ItemType'], _drop['ItemID'], _drop['ItemNum']] , drop_items )

                old_star_rate[_drop_id] = 0
            else:
                old_star_rate[_drop_id] += _drop['RateAdd']
        yield redis.hset( HASH_DUNGEON_DROP_RATE % dungeon_id, self.cid, dumps( old_rate ) )

        defer.returnValue( drop_items )

    @defer.inlineCallbacks
    def get_dungeon_drop(self, drop_items, way_type, way_others=''):
        ''' 获取怪物组战斗胜利后 掉落的道具 '''
        dungeon_drop_items=[]

        for _item_type, _item_id, _item_num in drop_items:
            # 掉落分魂碎片、普通道具
            _model = ITEM_MODELs.get(_item_type, None)
            if not _model:
                log.error('Unknown item type. ItemType: {0}.'.format( _item_type ))
                continue
            res_err, value = yield _model(self.user, ItemID=_item_id, ItemNum=_item_num, AddType=way_type, WayOthers=way_others, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    dungeon_drop_items = total_new_items( _v, dungeon_drop_items )

        defer.returnValue( dungeon_drop_items )

    @defer.inlineCallbacks
    def get_battle_reward(self, battle_type, status, activescene_id):
        '''
        @param : battle_type-3:经验熊猫; 4:经验宝物; 5:打土豪
            当type=5时, status值为对土豪的有效伤害值
        @param : 战斗结果 status 0:fail, 1:success
        '''
        if activescene_id != self.old_activescene_id:
            log.error('Battle data error. old_activescene_id: {0}, activescene_id: {1}.'.format( self.old_activescene_id, activescene_id ))
            #defer.returnValue( REQUEST_LIMIT_ERROR )

        # 每日挑战次数限制
        yield self.system_daily_reset()

        self.revive_count       = 0
        self.old_activescene_id = 0

        # 战斗失败
        if not status:
            if battle_type == FIGHT_TYPE_PANDA:
                fight_count = self.activescene.panda_free + self.activescene.panda_buyed
                defer.returnValue( (battle_type, status, 0, 0, fight_count, [], 0, 0, 0, self.user.base_att.energy) )
            elif battle_type == FIGHT_TYPE_TREASURE:
                fight_count = self.activescene.treasure_free + self.activescene.treasure_buyed
                defer.returnValue( (battle_type, status, 0, 0, fight_count, [], 0, 0, 0, self.user.base_att.energy) )
            elif battle_type == FIGHT_TYPE_TREE:
                pass
            else:
                log.error('Unknown battle_type: {0}.'.format( battle_type ))
                defer.returnValue( REQUEST_LIMIT_ERROR )

        golds_reward = 0
        activescene_drop_items = []
        # 扣挑战次数
        if battle_type == FIGHT_TYPE_PANDA:
            if self.activescene.panda_buyed > 0:
                self.activescene.panda_buyed -= 1
            elif self.activescene.panda_free > 0:
                self.activescene.panda_free -= 1
            else:
                log.error('No fight count. panda_free: {0}, panda_buyed: {1}.'.format( self.activescene.panda_free, self.activescene.panda_buyed ))
                defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
            fight_count = self.activescene.panda_free + self.activescene.panda_buyed
            # 获取怪物组掉落, star默认为1
            drop_items = yield self.dungeon_star_drop( activescene_id, 1 )
            # 新增掉落
            way_others = str((FIGHT_TYPE_PANDA, activescene_id, 1))
            activescene_drop_items = yield self.get_dungeon_drop( drop_items, WAY_ACTIVESCENE_PANDA_FIGHT, way_others )

        elif battle_type == FIGHT_TYPE_TREASURE:
            if self.activescene.treasure_buyed > 0:
                self.activescene.treasure_buyed -= 1
            elif self.activescene.treasure_free > 0:
                self.activescene.treasure_free -= 1
            else:
                log.error('No fight count. treasure_free: {0}, treasure_buyed: {1}.'.format( self.activescene.treasure_free, self.activescene.treasure_buyed ))
                defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
            fight_count = self.activescene.treasure_free + self.activescene.treasure_buyed
            # 获取怪物组掉落, star默认为1
            drop_items = yield self.dungeon_star_drop( activescene_id, 1 )
            # 新增掉落
            way_others = str((FIGHT_TYPE_TREASURE, activescene_id, 1))
            activescene_drop_items = yield self.get_dungeon_drop( drop_items, WAY_ACTIVESCENE_TREASURE_FIGHT, way_others )

        elif battle_type == FIGHT_TYPE_TREE:
            if self.activescene.tree_buyed > 0:
                self.activescene.tree_buyed -= 1
            elif self.activescene.tree_free > 0:
                self.activescene.tree_free -= 1
            else:
                log.error('No fight count. tree_free: {0}, tree_buyed: {1}.'.format( self.activescene.tree_free, self.activescene.tree_buyed ))
                defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
            fight_count = self.activescene.tree_free + self.activescene.tree_buyed
            # 计算金币
            golds_reward = int((status+9) / 10)
            gold_tree_conf = get_gold_tree_conf()
            for _d, _g in gold_tree_conf:
                if status < _d:
                    break
                golds_reward += _g
            self.user.get_golds( golds_reward, WAY_ACTIVESCENE_TREE_FIGHT )
        else:
            log.error('Unknown battle_type: {0}.'.format( battle_type ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_4, 1 )
        # add syslog
        str_drop_items = str(activescene_drop_items).replace('[', '(')
        str_drop_items = str_drop_items.replace(']', ')')
        syslogger(LOG_SCENE_BATTLE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, battle_type, status, activescene_id, 1, 0, 0, golds_reward, str_drop_items)

        defer.returnValue( (battle_type, status, 0, 0, fight_count, activescene_drop_items, golds_reward, 0, 0, self.user.base_att.energy) )

    @defer.inlineCallbacks
    def buy_count(self, battle_type):
        '''
        @summary: 购买挑战次数,价格=基础价格*购买次数
        '''
        vip_conf = get_vip_conf( self.user.base_att.vip_level )
        if not vip_conf:
            log.error('No vip conf. vip_level: {0}.'.format( self.user.base_att.vip_level ))
            defer.returnValue( NOT_FOUND_CONF )
        yield self.system_daily_reset()
        if battle_type == FIGHT_TYPE_PANDA:
            # 还有剩余挑战次数
            if (self.activescene.panda_free+self.activescene.panda_buyed > 0):
                log.error('User has fight count. panda_free: {0}, panda_buyed: {1}.'.format( self.activescene.panda_free, self.activescene.panda_buyed ))
                defer.returnValue( HAVE_NUM_TO_USE )
            # 已购买次数达上限
            if self.activescene.panda_left_buy >= vip_conf['ActiveSceneCount']:
                log.error('No panda fight count could buy today. cid:{0}, vip_level:{1}.'.format( self.cid, self.user.vip_level ))
                defer.returnValue( BUY_MAX_NUM_ERROR )
            # 钻石不足
            conf = get_activescene_conf( ACTIVE_PANDA_ID )
            if not conf:
                log.error('Can not find conf. activescene_id: {0}.'.format( ACTIVE_PANDA_ID ))
                defer.returnValue( NOT_FOUND_CONF )
            need_credits = (self.activescene.panda_left_buy + 1) * conf['Price']
            if self.user.base_att.credits < need_credits:
                log.error('Credits not enough. need: {0}, cur: {1}.'.format( need_credits, self.user.base_att.credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            yield self.user.consume_credits(need_credits, WAY_ACTIVESCENE_PANDA_FIGHT)
            self.activescene.panda_left_buy += 1
            self.activescene.panda_buyed    += 1

            defer.returnValue( ((self.activescene.panda_free + self.activescene.panda_buyed), self.activescene.panda_left_buy, self.user.base_att.credits) )
        elif battle_type == FIGHT_TYPE_TREASURE:
            # 还剩余有挑战次数
            if (self.activescene.treasure_free+self.activescene.treasure_buyed > 0):
                log.error('User has fight count. treasure_free: {0}, treasure_buyed: {1}.'.format( self.activescene.treasure_free, self.activescene.treasure_buyed ))
                defer.returnValue( HAVE_NUM_TO_USE )
            # 剩余购买次数不足
            if self.activescene.treasure_left_buy >= vip_conf['ActiveSceneCount']:
                log.error('No treasure fight count could buy today. cid:{0}, vip_level:{1}.'.format( self.cid, self.user.vip_level ))
                defer.returnValue( BUY_MAX_NUM_ERROR )
            # 钻石不足
            conf = get_activescene_conf( ACTIVE_TREASURE_ID )
            if not conf:
                log.error('No conf. activescene_id: {0}.'.format( ACTIVE_TREASURE_ID ))
                defer.returnValue( NOT_FOUND_CONF )
            need_credits = (self.activescene.treasure_left_buy + 1) * conf['Price']
            if self.user.base_att.credits < need_credits:
                log.error('Credits not enough. need: {0}, cur: {1}.'.format( need_credits, self.user.base_att.credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            yield self.user.consume_credits(need_credits, WAY_ACTIVESCENE_TREASURE_FIGHT)
            self.activescene.treasure_left_buy += 1
            self.activescene.treasure_buyed    += 1

            defer.returnValue( ((self.activescene.treasure_free + self.activescene.treasure_buyed), self.activescene.treasure_left_buy, self.user.base_att.credits) )
        elif battle_type == FIGHT_TYPE_TREE:
            # 还剩余有挑战次数
            if (self.activescene.tree_free+self.activescene.tree_buyed > 0):
                log.error('User has fight count. tree_free: {0}, tree_buyed: {1}.'.format( self.activescene.tree_free, self.activescene.tree_buyed ))
                defer.returnValue( HAVE_NUM_TO_USE )
            # 剩余购买次数不足
            if self.activescene.tree_left_buy >= vip_conf['ActiveSceneCount']:
                log.error('No tree fight count could buy today. cid:{0}, vip_level:{1}.'.format( self.cid, self.user.vip_level ))
                defer.returnValue( BUY_MAX_NUM_ERROR )
            # 钻石不足
            conf = get_activescene_conf( ACTIVE_TREE_ID )
            if not conf:
                log.error('No conf. activescene_id: {0}.'.format( ACTIVE_TREE_ID ))
                defer.returnValue( NOT_FOUND_CONF )
            need_credits = (self.activescene.tree_left_buy + 1) * conf['Price']
            if self.user.base_att.credits < need_credits:
                log.error('Credits not enough. need: {0}, cur: {1}.'.format( need_credits, self.user.base_att.credits ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            yield self.user.consume_credits(need_credits, WAY_ACTIVESCENE_TREE_FIGHT)
            self.activescene.tree_left_buy += 1
            self.activescene.tree_buyed    += 1

            defer.returnValue( ((self.activescene.tree_free + self.activescene.tree_buyed), self.activescene.tree_left_buy, self.user.base_att.credits) )
        else:
            log.error('Unknown battle_type: {0}.'.format( battle_type ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

    def battle_revive(self, battle_type):
        '''
        @summary: 复活初始价格为200金币, 价格=复活次数*初始价格
             同一场战斗中不同波数复活次数要累计 
        '''
        need_golds = (self.revive_count + 1)*REVIVE_BASIC_GOLDS
        if (self.user.base_att.golds < need_golds):
            log.error('Golds not enough. need: {0}, cur: {1}.'.format( need_golds, self.user.base_att.golds ))
            return CHAR_GOLD_NOT_ENOUGH

        self.user.base_att.golds -= need_golds
        self.revive_count += 1

        return [self.user.base_att.golds]

