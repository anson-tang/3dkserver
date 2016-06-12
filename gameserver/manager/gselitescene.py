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
from system   import get_vip_conf, get_elitescene_conf, get_drop_conf
from syslogger import syslogger

from twisted.internet       import defer
from models.item            import *
from models.characterserver import gs_load_table_data, gs_create_table_data
from manager.gsattribute    import GSAttribute
from table_fields           import TABLE_FIELDS


class GSEliteSceneMgr(object):
    _table = 'elitescene'
    _fields = TABLE_FIELDS['elitescene'][0]

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        self.load_flag = False

        # 单次战斗中伙伴复活的次数
        self.revive_count = 0
        # 战斗中的精英副本ID
        self.old_elitescene_id = 0
        self.elitescene = GSAttribute(user.cid, GSEliteSceneMgr._table, user.cid)
        # 已战斗胜利的精英副本ID列表
        self.passed_elitescene_ids = []

    @defer.inlineCallbacks
    def load(self):
        if not self.load_flag:
            try:
                table_data = yield gs_load_table_data(self.cid, GSEliteSceneMgr._table)
                # 注意在收到返回消息后才能赋值
                self.load_flag = True

                if table_data:
                    table_data = dict(zip(GSEliteSceneMgr._fields, table_data))
                    self.elitescene.updateGSAttribute( False,  **table_data)
                else:
                    yield self.new()
                _data = yield redis.hget(HASH_ELITESCENE_PASSED, self.cid)
                if _data:
                    self.passed_elitescene_ids = loads(_data)
            except Exception as e:
                log.error( 'Exception raise. e: {0}.'.format( e ))

    def sync_to_cs(self):
        if self.elitescene:
            self.elitescene.syncToCS()

    @defer.inlineCallbacks
    def new(self):
        dt_now = datetime.now()
        kwargs = dict(zip(GSEliteSceneMgr._fields[1:], [self.cid, ELITESCENE_FIGHT_COUNT, 0, 0, dt_now]))#datetime2string(dt_now)]))
        create_data = yield gs_create_table_data(self.cid, GSEliteSceneMgr._table, **kwargs)
        if create_data:
            create_data = dict(zip(GSEliteSceneMgr._fields, create_data))
            self.elitescene.updateGSAttribute( False,  **create_data)
        else: # 新增数据失败
            self.load_flag = False

        defer.returnValue( NO_ERROR )

    def system_daily_reset(self):
        '''
        @summary: 每天24点系统重置精英副本数据, 含免费挑战次数、剩余可够买的次数、更新时间
        '''
        dt_now  = datetime.now()
        dt_last = self.elitescene.last_datetime
        if dt_now.date() != dt_last.date():
            self.elitescene.left_buy_fight = 0
            self.elitescene.free_fight    = ELITESCENE_FIGHT_COUNT
            self.elitescene.last_datetime = dt_now

    @defer.inlineCallbacks
    def elitescene_data(self):
        '''
        @summary: 获取精英副本的基本信息
        '''
        yield self.load()
        self.system_daily_reset()
        conf = get_vip_conf( self.user.vip_level )
        left_buy_fight = conf['EliteSceneCount'] if conf else 0
        left_buy_fight = left_buy_fight - self.elitescene.left_buy_fight if left_buy_fight > self.elitescene.left_buy_fight else 0

        defer.returnValue( (self.elitescene.free_fight + self.elitescene.buyed_fight, left_buy_fight, self.passed_elitescene_ids) )

    @defer.inlineCallbacks
    def start_battle(self, elitescene_id):
        '''
        @summary: 记录玩家的战斗信息
        '''
        # 检查战斗条件是否满足
        errorno = yield self.check_battle_limit( elitescene_id )
        defer.returnValue( errorno )

    @defer.inlineCallbacks
    def check_battle_limit(self, elitescene_id):
        ''' 检查战斗的条件是否满足 '''
        conf = get_elitescene_conf( elitescene_id )
        if not conf:
            log.error('Unknown elitescene conf. id: {0}.'.format( elitescene_id ))
            defer.returnValue( NOT_FOUND_CONF )
        # 检查精英副本是否开启
        _scene_passed = yield self.user.scene_mgr.check_scene_passed( conf['SceneID'] )
        if 0 == _scene_passed:
            log.error('Scene need passed. cid: {0}, scene_id: {1}, elitescene_id: {2}.'.format( self.cid, conf['SceneID'], elitescene_id ))
            defer.returnValue( SCENE_NEED_PASSED )
        # 检查精英副本的前置副本是否已通关
        if conf['PrepEliteSceneID'] and conf['PrepEliteSceneID'] not in self.passed_elitescene_ids:
            log.error('PrepEliteSceneID<{0}> need win. cid: {1}.'.format( conf['PrepEliteSceneID'], self.cid ))
            defer.returnValue( PREP_ELITESCENE_NEED_WIN )
        # 检查玩家的等级限制
        if conf['NeedRoleLevel'] > self.user.base_att.level:
            log.error('User level limit. cid: {0}, need: {1}, cur: {2}.'.format( self.cid, conf['NeedRoleLevel'], self.user.base_att.level ))
            defer.returnValue( CHAR_LEVEL_LIMIT )

        self.system_daily_reset()
        # 每日挑战次数限制
        if (self.elitescene.free_fight + self.elitescene.buyed_fight < 1):
            log.error('No fight count. cid: {0}, free_fight: {1}, buyed_fight: {2}.'.format( self.cid, self.elitescene.free_fight, self.elitescene.buyed_fight ))
            defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )

        self.revive_count = 0
        self.old_elitescene_id = elitescene_id

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
            add_rate   = old_star_rate.get(_drop_id, 0)
            _drop_rate = _drop['RateStart'] + add_rate
            # 单次增加的封顶概率
            if _drop_rate > _drop['RateMax']:
                _drop_rate = _drop['RateMax']
            # 掉落概率是万分比
            rand_int = random.randint(0, 10000)
            # _drop['QuestID'] 未处理
            # 当前随机值 不大于 配置的掉落概率值时掉落
            if rand_int <= _drop_rate:
                drop_items = add_new_items( [_drop['ItemType'], _drop['ItemID'], _drop['ItemNum']] , drop_items )

                old_star_rate[_drop_id] = 0
            else:
                old_star_rate[_drop_id] = old_star_rate.setdefault(_drop_id, 0) + _drop['RateAdd']
        yield redis.hset( HASH_DUNGEON_DROP_RATE % dungeon_id, self.cid, dumps( old_rate ) )

        defer.returnValue( drop_items )

    @defer.inlineCallbacks
    def get_dungeon_drop(self, drop_items, way_others=''):
        ''' 获取怪物组战斗胜利后 掉落的道具 '''
        dungeon_drop_items=[]

        for _item_type, _item_id, _item_num in drop_items:
            # 掉落分魂碎片、普通道具
            _model = ITEM_MODELs.get(_item_type, None)
            if not _model:
                log.error('Unknown item type. ItemType: {0}.'.format( _item_type ))
                continue
            res_err, value = yield _model(self.user, ItemID=_item_id, ItemNum=_item_num, AddType=WAY_ELITESCENE_DROP, WayOthers=way_others, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    dungeon_drop_items = total_new_items( _v, dungeon_drop_items )

        defer.returnValue( dungeon_drop_items )

    @defer.inlineCallbacks
    def get_battle_reward(self, status, elitescene_id):
        '''
        @param  : 战斗结果 status 0:fail, 1:success
        '''
        self.revive_count      = 0
        self.old_elitescene_id = 0
        ## 检查战斗条件是否满足
        #errorno = yield self.check_battle_limit( elitescene_id )
        #if errorno:
        #    defer.returnValue( errorno )
        # 战斗失败
        if not status:
            defer.returnValue( (2, status, 0, 0, self.elitescene.free_fight + self.elitescene.buyed_fight, [], 0, 0, 0, self.user.base_att.energy) )
        # 精英副本奖励金币、仙魂
        golds_reward, soul_reward = 0, 0
        # config
        conf = get_elitescene_conf( elitescene_id )
        if conf:
            golds_reward, soul_reward = conf['Gold'], conf['Soul']
        # 扣挑战次数
        if self.elitescene.buyed_fight > 0:
            self.elitescene.buyed_fight -= 1
        elif self.elitescene.free_fight > 0:
            self.elitescene.free_fight -= 1
        else:
            log.error('No fight count. free_fight: {0}, buyed_fight: {1}.'.format( self.elitescene.free_fight, self.elitescene.buyed_fight ))
            defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )

        # 获取怪物组掉落, star默认为1
        drop_items = yield self.dungeon_star_drop( elitescene_id, 1 )
        # 新增掉落
        way_others = str((FIGHT_TYPE_ELITE, elitescene_id, 1))
        elitescene_drop_items = yield self.get_dungeon_drop( drop_items, way_others )
        # 发放奖励
        if golds_reward > 0:
            #self.user.base_att.golds += golds_reward
            self.user.get_golds( golds_reward, WAY_ELITESCENE_BATTLE )
        if soul_reward > 0:
            self.user.base_att.soul  += soul_reward

        # 更新已胜利的精英副本ID列表
        if elitescene_id not in self.passed_elitescene_ids:
            self.passed_elitescene_ids.append( elitescene_id )
            yield redis.hset( HASH_ELITESCENE_PASSED, self.cid, dumps(self.passed_elitescene_ids) )
        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_2, 1 )
        # 开服七天
        self.passed_elitescene_ids.sort()
        yield self.user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_12, self.passed_elitescene_ids[-1])
        # add syslog
        #成就
        yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_12, self.passed_elitescene_ids[-1])
        str_drop_items = str(elitescene_drop_items).replace('[', '(')
        str_drop_items = str_drop_items.replace(']', ')')
        syslogger(LOG_SCENE_BATTLE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, FIGHT_TYPE_ELITE, status, elitescene_id, 1, 0, soul_reward, golds_reward, str_drop_items)

        defer.returnValue( (2, status, 0, 0, self.elitescene.free_fight + self.elitescene.buyed_fight, elitescene_drop_items, golds_reward, soul_reward, 0, self.user.base_att.energy) )

    @defer.inlineCallbacks
    def buy_count(self):
        '''
        @summary: 购买挑战次数
               每购买1次额外挑战次数，需要花费10钻石
        '''
        if self.user.base_att.credits < 10:
            log.error('Credits not enough. need: 10, cur: {0}.'.format( self.user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        # 还剩余有挑战次数
        if (self.elitescene.free_fight + self.elitescene.buyed_fight > 0):
            log.error('User has more than 1 fight count. free_fight: {0}, buyed_fight: {1}.'.format( self.elitescene.free_fight, self.elitescene.buyed_fight ))
            defer.returnValue( HAVE_NUM_TO_USE )
        # 判断VIP等级对应的可购买次数限制
        self.system_daily_reset()

        conf = get_vip_conf( self.user.vip_level )
        left_buy_fight = conf['EliteSceneCount'] if conf else 0
        left_buy_fight = left_buy_fight - self.elitescene.left_buy_fight if left_buy_fight > self.elitescene.left_buy_fight else 0
        if left_buy_fight < 1:
            log.error('No fight count could buy today.')
            defer.returnValue( BUY_MAX_NUM_ERROR )
        left_buy_fight -= 1
 
        yield self.user.consume_credits(10, WAY_ELITESCENE_FIGHT)
        self.elitescene.left_buy_fight += 1
        self.elitescene.buyed_fight += 1

        defer.returnValue( ((self.elitescene.free_fight + self.elitescene.buyed_fight), left_buy_fight, self.user.base_att.credits) )


    def battle_revive(self):
        '''
        @summary: 复活初始价格为200金币, 价格=复活次数*初始价格
             同一场战斗中不同波数复活次数要累计 
        '''
        need_golds = (self.revive_count + 1)*REVIVE_BASIC_GOLDS
        #log.info('For Test. revive_count: {0}, need_golds: {1}, cur_golds: {2}.'.format( self.revive_count, need_golds, self.user.base_att.golds ))
        if (self.user.base_att.golds < need_golds):
            log.error('Golds not enough. need: {0}, cur: {1}.'.format( need_golds, self.user.base_att.golds ))
            return CHAR_GOLD_NOT_ENOUGH

        #self.user.base_att.golds -= need_golds
        self.user.consume_golds( need_golds, WAY_ELITESCENE_REVIVE )
        self.revive_count += 1

        return [self.user.base_att.golds]

