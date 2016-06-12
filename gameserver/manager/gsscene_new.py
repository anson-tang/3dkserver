#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from datetime import datetime
from time     import time, strftime, localtime
from log      import log
from marshal  import loads, dumps     

from errorno  import *
from constant import *
from redis    import redis
from utils    import split_items, timestamp_is_today
from syslogger import syslogger

from twisted.internet       import defer, reactor
from system                 import get_scene_dungeon, get_all_scene_dungeon, get_monster_conf, \
        get_drop_conf, get_item_by_itemid, get_all_scene, get_scene_star_reward, get_vip_conf, \
        get_scene_conf, get_game_limit_value, get_scene_sweep_cost_conf, get_scene_reset_conf
from manager.gsattribute    import GSAttribute
from models.item            import *
from models.award_center    import g_AwardCenterMgr
from handler.character      import gs_offline_login, gs_offline_logout


@defer.inlineCallbacks
def load_scene_user_data(cid):
    ''' 
    @summary: 加载玩家的基本信息。
    '''
    _user_data = []
    _offline_user = yield gs_offline_login( cid )
    if _offline_user:
        _ = yield _offline_user.scene_mgr.get_scene(0)
        _user_data = [cid, _offline_user.lead_id, _offline_user.level, _offline_user.nick_name, \
                _offline_user.might, _offline_user.scene_mgr.max_scene_id]
        reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, cid)

    defer.returnValue( _user_data )



class GSSceneMgr(object):
    '''
    @summary: 副本
    @param  : dungeon_star 1-simple 2-middle 3-difficult
    '''
    _table     = 'scene'

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        # data format: {scene_id: {dungeon_id: gsattrib, ...}, ...}
        self.__scenes  = None
        
        # 副本战斗的记录
        self.cur_scene_id     = 0
        self.cur_dungeon_id   = 0
        self.cur_dungeon_star = 0

        # 副本的星级数量
        self.star_rewarded = None
        # 当前副本的总星数
        self.total_star = 0
        # 当前可挑战的最大副本ID
        self.max_scene_id = 0

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def _load(self):
        if self.__scenes is None:
            if not self.__loading:
                self.__loading = True
                gsattribs     = yield GSAttribute.load( self.cid, GSSceneMgr._table )
                # 注意在收到返回消息后才能赋值
                self.__scenes = {}
                for gsattrib in gsattribs.itervalues():
                    if self.__scenes.has_key( gsattrib.scene_id ):
                        _scene_data = self.__scenes[gsattrib.scene_id]
                        _scene_data[gsattrib.dungeon_id] = gsattrib
                    else:
                        _scene_data = {gsattrib.dungeon_id: gsattrib}
                        self.__scenes[gsattrib.scene_id] = _scene_data
                    self.total_star += gsattrib.dungeon_star
                    if gsattrib.scene_id > self.max_scene_id:
                        self.max_scene_id = gsattrib.scene_id

                for d in self.__defers:
                    d.callback(True)

                self.__loading = False
                self.__defers  = []
            else:
                d = defer.Deferred()
                self.__defers.append(d)
                yield d

    def sync_to_cs(self):
        if self.__scenes:
            for scene in self.__scenes.itervalues():
                for attrib in scene.itervalues():
                    attrib.syncToCS()

    @defer.inlineCallbacks
    def load_star_rewarded(self):
        ''' 加载副本已领奖的星数 '''
        if self.star_rewarded is None:
            self.star_rewarded = {}
            rewarded_data = yield redis.hget( HASH_SCENE_STAR_REWARDED, self.cid )
            if rewarded_data:
                self.star_rewarded = loads( rewarded_data )

    @defer.inlineCallbacks
    def get_star_rewarded(self, scene_id):
        ''' 获取已领奖的副本星数记录 '''
        yield self.load_star_rewarded()
        defer.returnValue( self.star_rewarded.get(scene_id, []) )

    @defer.inlineCallbacks
    def update_star_rewarded(self, scene_id, star_count):
        ''' 更新已领奖的副本星数记录 '''
        old_star_rewarded = yield self.get_star_rewarded(scene_id)
        if star_count not in old_star_rewarded:
            self.star_rewarded.setdefault(scene_id, []).append( star_count )
            yield redis.hset( HASH_SCENE_STAR_REWARDED, self.cid, dumps( self.star_rewarded) )
        else:
            log.error('scene star had been rewarded.')

    @defer.inlineCallbacks
    def get_dungeon(self, scene_id, dungeon_id):
        yield self._load()
        gsattrib = self.__scenes.get(scene_id, {}).get(dungeon_id, None)
        defer.returnValue( gsattrib )

    @defer.inlineCallbacks
    def get_scene(self, scene_id):
        yield self._load()
        defer.returnValue( self.__scenes.get(scene_id, {}) )

    @defer.inlineCallbacks
    def create_table_data(self, scene_id, dungeon_id, dungeon_star=0, dungeon_today_count=0, dungeon_last_time=0, dungeon_award=0):
        gsattrib = GSAttribute( self.cid, GSSceneMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, scene_id=scene_id, dungeon_id=dungeon_id, dungeon_star=dungeon_star, dungeon_today_count=dungeon_today_count, dungeon_award=dungeon_award, dungeon_last_time=dungeon_last_time )
        if res_err:
            log.error('GSSceneMgr create table data error. ')
            defer.returnValue( (UNKNOWN_ERROR, None) )

        if self.__scenes.has_key( gsattrib.scene_id ):
             _scene_data = self.__scenes[gsattrib.scene_id]
             _scene_data[gsattrib.dungeon_id] = gsattrib
        else:
             _scene_data = {gsattrib.dungeon_id: gsattrib}
             self.__scenes[gsattrib.scene_id] = _scene_data
        defer.returnValue( (NO_ERROR, gsattrib) )

    @defer.inlineCallbacks
    def check_scene_passed(self, scene_id):
        '''
        @summary: 判断某副本是否已通关
        @param  : passed(通关状态): 0: 未通关, 1: 已通关
        '''
        _passed = 0
        _scene  =  yield self.get_scene( scene_id )
        if _scene:
            for gsattrib in _scene.itervalues():
                if gsattrib.dungeon_star <= 0:
                    _passed = 0
                    break
            else:
                _passed = 1

        defer.returnValue( _passed )

    @defer.inlineCallbacks
    def all_scene_group(self):
        '''
        @summary: 返回Array: [scene_id, passed, had_star]
            其中 passed(通关状态): 0: 未通关, 1: 已通关
            星数与难度对应关系 1:simple, 2:middle, 3:difficulty
        '''
        yield self._load()
        _all_scene = []
        scene_conf = get_all_scene()
        cur_date   = datetime.now()
        for scene_id, _value in scene_conf.iteritems():
            if self.user.base_att.level < _value['LowLevel']:
                continue
            _pre_id   = _value['PreposeScene']
            _pre_pass = yield self.check_scene_passed( _pre_id )
            if 0 != _pre_id and 0 == _pre_pass:
                continue
            _scene  =  yield self.get_scene( scene_id )
            if not _scene:
                res_err = yield self.new_dungeon_group( scene_id )
                if res_err:
                    log.error('new_dungeon_group error. scene_id: {0}, res_err: {1}.'.format( scene_id, res_err ))
                    continue
                _scene  =  yield self.get_scene( scene_id )
                if not _scene:
                    log.error('get scene error. scene_id: {0}.'.format( scene_id ))
                    continue
            _total_count = 0
            for dungeon_conf in _value['dungeons']:
                _total_count += dungeon_conf['RushMax']
            _passed    = 1 # 初值已通关
            _had_star  = 0 # 获得的星星数量
            _had_count = 0 # 该副本今日已挑战的总次数
            for gsattrib in _scene.itervalues():
                if gsattrib.dungeon_star <= 0:
                    _passed = 0
                _had_star += gsattrib.dungeon_star
                self.check_today_count( gsattrib, cur_date )
                _had_count += gsattrib.dungeon_today_count
            # 全扫荡的标志位 0-不能全扫荡 1-可以全扫荡
            _status = 0
            if  _total_count > _had_count and _value['StarNum'] <= _had_star:
                _status = 1
            _all_scene.append( [scene_id, _passed, _had_star, _status] )

        defer.returnValue( _all_scene )
 
    @defer.inlineCallbacks
    def new_dungeon_group(self, scene_id):
        '''
        @summary: 初始化scene_id下所有的dungeon 
        '''
        dungeons = get_all_scene_dungeon(scene_id)
        if not dungeons:
            log.error('Can not find scene dungeon conf. scene_id: {0}.'.format( scene_id ))
            defer.returnValue( NOT_FOUND_CONF )

        for _d in dungeons.itervalues():
            yield self.create_table_data( scene_id, _d['DungeonID'] )

        defer.returnValue( NO_ERROR )

    def check_today_count(self, gsattrib, cur_date):
        last_date = gsattrib.dungeon_last_time

        # 不是同一天且挑战次数大于0时, 将挑战次数清零
        if last_date.date() != cur_date.date() and gsattrib.dungeon_today_count > 0:
            gsattrib.dungeon_today_count = 0

    @defer.inlineCallbacks
    def all_dungeon_group(self, scene_id):
        '''
        @summary: 获取副本内怪物信息
        '''
        #yield self._load()
        groups   = []
        dungeons = yield self.get_scene( scene_id )
        if not dungeons:
            res_err = yield self.new_dungeon_group( scene_id )
            dungeons = yield self.get_scene( scene_id )
            if not dungeons:
                log.error('Can not find scene dungeon conf. scene_id: {0}.'.format( scene_id ))
                defer.returnValue( groups )

        cur_date  = datetime.now()
        for _d in dungeons.itervalues():
            self.check_today_count( _d, cur_date )
            groups.append( (_d.dungeon_id, _d.dungeon_star, _d.dungeon_today_count) )

        defer.returnValue( groups )

    @defer.inlineCallbacks
    def all_dungeon_group_new(self, scene_id):
        '''
        @summary: 获取副本内怪物信息
        '''
        #yield self._load()
        groups   = []
        dungeons = yield self.get_scene( scene_id )
        if not dungeons:
            res_err = yield self.new_dungeon_group( scene_id )
            dungeons = yield self.get_scene( scene_id )
            if not dungeons:
                log.error('Can not find scene dungeon conf. scene_id: {0}.'.format( scene_id ))
                defer.returnValue( groups )

        cur_date  = datetime.now()
        for _d in dungeons.itervalues():
            self.check_today_count( _d, cur_date )
            groups.append( (_d.dungeon_id, _d.dungeon_star, _d.dungeon_today_count, _d.dungeon_award) )

        defer.returnValue( groups )

    @defer.inlineCallbacks
    def multi_dungeon_group(self, scene_ids):
        '''
        @summary: 获取多个副本的怪物信息
        '''
        multi_scene = []
        scene_ids   = {}.fromkeys(scene_ids).keys()
        all_scene   = yield self.all_scene_group()
        for _scene in all_scene:
            if _scene[0] not in scene_ids:
                continue
            groups = yield self.all_dungeon_group_new( _scene[0] )
            multi_scene.append( [_scene[0], _scene[1], _scene[2], groups] )

        defer.returnValue( multi_scene )

    @defer.inlineCallbacks
    def start_battle(self, scene_id, dungeon_id, dungeon_star):
        '''
        @summary: 记录玩家的战斗信息
        '''
        if dungeon_star not in DUNGEON_STAR:
            log.error('Dungeon star error.')
            defer.returnValue( CLIENT_DATA_ERROR )

        dungeon = yield self.get_dungeon( scene_id, dungeon_id )
        if not dungeon:
            log.error('Unknown dungeon id.')
            defer.returnValue( UNKNOWN_ERROR )

        dungeon_conf = get_scene_dungeon( scene_id, dungeon_id )
        if not dungeon_conf:
            log.error('Unknown dungeon conf.')
            defer.returnValue( NOT_FOUND_CONF )
        
        # 每天挑战次数限制
        if dungeon.dungeon_today_count > dungeon_conf['RushMax']:
            log.error('dungeon today count limit. today count: {0}, rush max: {1}.'.format( dungeon.dungeon_today_count, dungeon_conf['RushMax'] ))
            defer.returnValue( DUNGEON_CHALLENGE_COUNT_LIMIT )
        
        self.cur_scene_id, self.cur_dungeon_id, self.cur_dungeon_star = scene_id, dungeon_id, dungeon_star
    
        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def dungeon_star_drop(self, dungeon_id, dungeon_star, flag=False):
        '''
        @summary: 怪物组不同难度掉落, 无conf则不用计算掉落
              2015-01-27 没有精力时，最终掉落概率=(基础概率+增加概率)* 1/3
        @param  : flag-True:无精力*1/3, False:有精力*1
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
            add_rate   = old_star_rate.get(_drop_id, old_star_rate.setdefault(_drop_id, 0))
            _drop_rate = _drop['RateStart'] + add_rate
            # 单次增加的封顶概率
            if _drop_rate > _drop['RateMax']:
                _drop_rate = _drop['RateMax']
            # 有无精力
            if flag:
                _drop_rate = _drop_rate / 3
            # 掉落概率是万分比
            rand_int = random.randint(0, 10000)
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
    def get_battle_reward(self, status, scene_id, dungeon_id, dungeon_star):
        '''
        @summary: 战斗结束领取奖励
        @param  : 战斗结果 status 0:lose, 1:win
        '''
        yield self._load()
        if scene_id != self.cur_scene_id or dungeon_id != self.cur_dungeon_id or dungeon_star != self.cur_dungeon_star:
            log.error('Player battle info not match. old_scene_id: {0}, old_dungeon_id: {1}, old_dungeon_star: {2}.'.format( self.cur_scene_id, self.cur_dungeon_id, self.cur_dungeon_star ))
            #defer.returnValue( REQUEST_LIMIT_ERROR )
 
        dungeon = yield self.get_dungeon( scene_id, dungeon_id )
        if not dungeon:
            log.error('Unknown dungeon id. scene_id: {0}, dungeon_id: {1}.'.format( scene_id, dungeon_id ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        self.cur_scene_id, self.cur_dungeon_id, self.cur_dungeon_star = 0, 0, 0

        # 战斗失败
        if not status:
            syslogger(LOG_SCENE_BATTLE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, 1, status, dungeon_id, dungeon_star, 0, 0, 0, '')
            defer.returnValue( (1, status, dungeon_id, dungeon.dungeon_star, dungeon.dungeon_today_count, [], 0, 0, 0, self.user.base_att.energy) )

        # monster奖励金币、仙魂、经验
        exp_reward, golds_reward, soul_reward = 0, 0, 0
        monster_conf = get_monster_conf(dungeon_id, dungeon_star)
        no_energy = False
        if monster_conf:
            # 策划修改-副本的精力消耗改为5点
            if self.user.base_att.energy >= 5:
                self.user.base_att.energy -= 5
                exp_reward = self.user.base_att.level * BATTLE_MONSTER_EXP_RATIO
            else:
                no_energy = True
                exp_reward = self.user.base_att.level
            soul_reward  = monster_conf['Soul']
            golds_reward = monster_conf['Money']
        else:
            log.error('Can not find monster.')
        # 获取怪物组掉落
        drop_items = yield self.dungeon_star_drop( dungeon_id, dungeon_star, no_energy )
        # 判断是否是第一次挑战更高星级难度
        if dungeon_star > dungeon.dungeon_star:
            dungeon.dungeon_star = dungeon_star
            # 新增混沌星数
            self.user.base_att.scene_star += 1
            # 新增副本总星数
            self.total_star += 1
            yield redis.zadd(SET_SCENE_CID_STAR, self.cid, -self.total_star)
            # 更新最大副本ID
            if scene_id > self.max_scene_id:
                self.max_scene_id = scene_id
            syslogger(LOG_SCENESTAR_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, 1, self.user.base_att.scene_star, dungeon_id, dungeon_star)
        dungeon.dungeon_today_count += 1
        dungeon.dungeon_last_time    = datetime.now()

        # 新增掉落
        way_others = str((FIGHT_TYPE_NORMAL, dungeon_id, dungeon_star))
        dungeon_drop_items = yield self.get_dungeon_drop( drop_items, way_others )

        # 发放奖励
        yield self.user.update_battle_attr( soul_reward, golds_reward, exp_reward )

        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_3, 1 )
        # 开服七天
        yield self.user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_3, dungeon_id)
        #成就
        yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_3, dungeon_id)
        yield self.user.achievement_mgr.update_alliance_level()
        # add syslog
        str_drop_items = str(dungeon_drop_items).replace('[', '(')
        str_drop_items = str_drop_items.replace(']', ')')
        syslogger(LOG_SCENE_BATTLE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, FIGHT_TYPE_NORMAL, status, dungeon_id, dungeon_star, exp_reward, soul_reward, golds_reward, str_drop_items)

        defer.returnValue( (1, status, dungeon_id, dungeon.dungeon_star, dungeon.dungeon_today_count, dungeon_drop_items, golds_reward, soul_reward, exp_reward, self.user.base_att.energy) )

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
            res_err, value = yield _model(self.user, ItemID=_item_id, ItemNum=_item_num, AddType=WAY_SCENE_DROP, WayOthers=way_others, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    dungeon_drop_items = total_new_items( _v, dungeon_drop_items )

        defer.returnValue( dungeon_drop_items )

    @defer.inlineCallbacks
    def scene_star_reward(self, scene_id, scene_star_count):
        ''' 领取副本宝箱奖励 '''
        had_star = 0
        scene    =  yield self.get_scene( scene_id )
        if scene:
            for gsattrib in scene.itervalues():
                had_star += gsattrib.dungeon_star
        # 判断能否领取奖励
        if scene_star_count > had_star:
            log.error('Can not get scene star reward. cur had star count: {0}.'.format( had_star ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        # 判断是否重复领取
        rewarded_data = yield self.get_star_rewarded( scene_id )
        if scene_star_count in rewarded_data:
            log.error('Scene star had been rewarded. rewarded_data: {0}.'.format( rewarded_data ))
            defer.returnValue( REPEAT_REWARD_ERROR )
        # 更新领奖记录
        yield self.update_star_rewarded(scene_id, scene_star_count)

        # 奖励conf
        reward_conf = get_scene_star_reward(scene_id, scene_star_count)
        if not reward_conf:
            log.error('Can not find star count reward conf.')
            defer.returnValue( NOT_FOUND_CONF )

        # 奖励
        items_return = []
        items_list   = split_items( reward_conf['Reward'] )
        for _type, _id, _num in items_list:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. item type: {0}.'.format( _type ))
                continue
            res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_SCENE_CHEST, WayOthers=str((scene_id, scene_star_count)), CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    items_return = total_new_items( _v, items_return )

        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def dungeon_reward(self, scene_id, dungeon_id):
        ''' 领取怪物组宝箱奖励 '''
        dungeon = yield self.get_dungeon(scene_id, dungeon_id)
        if not dungeon:
            log.error('Unknown dungeon id. scene_id: {0}, dungeon_id: {1}.'.format( scene_id, dungeon_id ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 判断能否领取奖励
        if 1 > dungeon.dungeon_star:
            defer.returnValue( SCENE_CHALLENGE_NEED_WIN )
        # 判断是否重复领取
        if 0 < dungeon.dungeon_award:
            defer.returnValue( REPEAT_REWARD_ERROR )
        # 缺少配置
        dungeon_conf = get_scene_dungeon( scene_id, dungeon_id )
        if not dungeon_conf or not dungeon_conf['AwardList']:
            log.error('Unknown dungeon conf. scene_id: {0}, dungeon_id: {1}.'.format( scene_id, dungeon_id ))
            defer.returnValue( NO_REWARD_ERROR )
        # 更新领奖记录
        dungeon.dungeon_award = 1
        # 奖励
        items_return = []
        for _type, _id, _num in dungeon_conf['AwardList']:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. item type: {0}.'.format( _type ))
                continue
            res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_SCENE_DUNGEON_CHEST, WayOthers=str((scene_id, dungeon_id)), CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    items_return = total_new_items( _v, items_return )

        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def win_streak(self, scene_id, dungeon_id, dungeon_star, battle_count):
        '''
        @summary: 连续战斗
        '''
        # 检查功能开放中连战的限制

        # 检查剩余可连续战斗次数
        vip_conf = get_vip_conf( self.user.base_att.vip_level )
        if not vip_conf:
            log.error('Unknown vip conf. cid:{0}, vip_level: {1}.'.format( self.cid, self.user.vip_level ))
            defer.returnValue( CHAR_VIP_LEVEL_LIMIT )
        cur_time = int(time())
        old_data = yield redis.hget(HASH_SCENE_COOLDOWN_TIME, self.cid)
        end_cooldown_time = int( old_data or 0 )
        if end_cooldown_time > cur_time:
            log.error('In CoolDown time. end time: {0}.'.format( end_cooldown_time ))
            defer.returnValue( IN_COOLDOWN_ERROR )
        end_cooldown_time = cur_time + vip_conf['DungeonTime']
        if battle_count > vip_conf['ContinuousBattles']:
            log.error('count limit. req_count: {0}, max_count: {1}.'.format( battle_count, vip_conf['ContinuousBattles'] ))
            defer.returnValue( DUNGEON_CHALLENGE_COUNT_LIMIT )

        dungeon = yield self.get_dungeon( scene_id, dungeon_id )
        if not dungeon:
            log.error('Unknown dungeon id.')
            defer.returnValue( UNKNOWN_ERROR )
        # 当前怪物组的数据
        dungeon_conf = get_scene_dungeon( scene_id, dungeon_id )
        if not dungeon_conf:
            log.error('Unknown dungeon conf.')
            defer.returnValue( NOT_FOUND_CONF )
        # 每天挑战次数限制
        if (dungeon.dungeon_today_count + battle_count) > dungeon_conf['RushMax']:
            log.error('count limit. req_count: {0}, today count: {1}, rush max: {2}.'.format( battle_count, dungeon.dungeon_today_count, dungeon_conf['RushMax'] ))
            defer.returnValue( DUNGEON_CHALLENGE_COUNT_LIMIT )
        # 怪物组conf
        monster_conf = get_monster_conf( dungeon_id, dungeon_star )
        if not monster_conf:
            log.error('Can not find monster.')
            defer.returnValue( NOT_FOUND_CONF )

        # 保存end cooldown time
        yield redis.hset( HASH_SCENE_COOLDOWN_TIME, self.cid, end_cooldown_time )
        # 连续n次战斗dungeon battle奖励金币、仙魂、经验
        exp_reward, soul_reward, golds_reward = 0, 0, 0
        dungeon.dungeon_today_count += battle_count
        dungeon.dungeon_last_time    = datetime.now()
        dungeon_drop_items = []
        drop_items = [] # [[uid, type, id, num], ...]
        for _c in range(0, battle_count):
            tmp_golds, tmp_soul, tmp_exp, no_energy = 0, 0, 0, False
            if self.user.base_att.energy >= 5:
                self.user.base_att.energy -= 5
                tmp_exp = self.user.base_att.level * BATTLE_MONSTER_EXP_RATIO
            else:
                no_energy = True
                tmp_exp = self.user.base_att.level
            tmp_soul    = monster_conf['Soul']
            tmp_golds   = monster_conf['Money']

            # 获取怪物组掉落
            tmp_drop = yield self.dungeon_star_drop( dungeon_id, dungeon_star, no_energy )
            dungeon_drop_items.append( [tmp_drop, tmp_golds, tmp_soul, tmp_exp] )
            for _t in tmp_drop:
                drop_items = add_new_items(_t, drop_items)
            # 发放奖励
            yield self.user.update_battle_attr( tmp_soul, tmp_golds, tmp_exp )
            exp_reward   += tmp_exp
            soul_reward  += tmp_soul
            golds_reward += tmp_golds
        # 玩家背包新增掉落
        way_others = str((FIGHT_TYPE_NORMAL, dungeon_id, dungeon_star))
        add_items = yield self.get_dungeon_drop( drop_items, way_others )

        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_3, battle_count )
        # add syslog
        str_drop_items = str(add_items).replace('[', '(')
        str_drop_items = str_drop_items.replace(']', ')')
        syslogger(LOG_SCENE_BATTLE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, FIGHT_TYPE_NORMAL, 1, dungeon_id, dungeon_star, exp_reward, soul_reward, golds_reward, str_drop_items)

        defer.returnValue( (dungeon_id, dungeon.dungeon_star, dungeon.dungeon_today_count, dungeon_drop_items, add_items, self.user.base_att.energy, end_cooldown_time) )

    @defer.inlineCallbacks
    def buy_cd_time(self):
        '''
        清除连战冷却时间 60s = 1 credits
        '''
        cur_time = int(time())
        old_data = yield redis.hget(HASH_SCENE_COOLDOWN_TIME, self.cid)
        end_cooldown_time = int( old_data or 0 )
        if end_cooldown_time <= cur_time:
            defer.returnValue( [self.user.base_att.credits] )

        need_credits = (end_cooldown_time - cur_time)
        if (need_credits % COOLDOWN_TIME_COST):
            need_credits = (need_credits / COOLDOWN_TIME_COST) + 1
        else:
            need_credits = (need_credits / COOLDOWN_TIME_COST)

        if need_credits > self.user.base_att.credits:
            log.error('Credits not enough. need: {0}, cur: {1}.'.format( total_credits, self.user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )

        yield self.user.consume_credits( need_credits, WAY_SCENE_CD_TIME )
        # 删除redis冷却时间记录
        yield redis.hdel( HASH_SCENE_COOLDOWN_TIME, self.cid )

        defer.returnValue( [self.user.base_att.credits] )

    @defer.inlineCallbacks
    def scene_all_sweep(self, scene_id, sweep_way=SCENE_SWEEP_CREDIT):
        ''' 对该副本的所有怪物组全扫荡, 掉落放入领奖中心
        '''
        # 检查玩家的VIP等级限制
        vip_conf = get_vip_conf( self.user.base_att.vip_level )
        if not vip_conf or not vip_conf['SceneALLSweep']:
            log.error('Not found vip conf. cid:{0}, vip_level:{1}.'.format( self.cid, self.user.vip_level ))
            defer.returnValue( CHAR_VIP_LEVEL_LIMIT )

        scene_conf = get_scene_conf(scene_id)
        if not scene_conf:
            defer.returnValue( NOT_FOUND_CONF )
        # 判断是否是满星副本
        had_star, left_dungeon_ids = 0, []
        scene    =  yield self.get_scene( scene_id )
        if not scene:
            defer.returnValue( NOT_FOUND_CONF )

        for dungeon_id, dungeon in scene.iteritems():
            had_star += dungeon.dungeon_star
            for dungeon_conf in scene_conf['dungeons']:
                if dungeon_conf['DungeonID'] != dungeon_id:
                    continue
                #if dungeon_conf['RushMax'] > dungeon.dungeon_today_count and dungeon_id not in left_dungeon_ids:
                if dungeon_conf['RushMax'] > dungeon.dungeon_today_count:
                    left_dungeon_ids.append( (dungeon_id, dungeon_conf['RushMax'] - dungeon.dungeon_today_count) )
        # 不是满星副本
        if had_star < scene_conf['StarNum']:
            defer.returnValue( SCENE_STAR_NOT_ENOUGH )
        # 判断是否还有挑战次数
        if not left_dungeon_ids:
            defer.returnValue( SCENE_CHALLENGE_COUNT_LIMIT )
        # 判断钻石数, 4-全部扫荡花费
        daily_info = yield self.get_scene_reset_daily()
        #all_sweep_cost = get_game_limit_value(4)
        #all_sweep_cost = int(all_sweep_cost) if all_sweep_cost else SCENE_ALL_SWEEP_COST
        items_return = []
        # 判断道具和钻石
        if sweep_way == SCENE_SWEEP_ITEM:
            # 扣道具 
            total_item, item_attribs = yield self.user.bag_item_mgr.get_items( ITEM_SCENE_SWEEP_ID )
            if 1 > total_item:
                defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            res_err, used_attribs = yield self.user.bag_item_mgr.use(ITEM_SCENE_SWEEP_ID, 1)
            if res_err:
                defer.returnValue( res_err )
            # used_attribs-已使用的道具
            for _a in used_attribs:
                items_return.append( [_a.attrib_id, ITEM_TYPE_ITEM, ITEM_SCENE_SWEEP_ID, _a.item_num] )
                # add syslog
                syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, \
                        self.user.alliance_id, _a.attrib_id, ITEM_SCENE_SWEEP_ID, 1, WAY_SCENE_ALL_SWEEP)
        else:
            all_sweep_cost = get_scene_sweep_cost_conf( daily_info[1]+1 )
            if self.user.credits < all_sweep_cost:
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            # 扣钻石
            self.user.consume_credits(all_sweep_cost, WAY_SCENE_ALL_SWEEP)
            # 副本 钻石扫荡次数累积
            daily_info[1] += 1
            yield redis.hset(HASH_SCENE_RESET_DAILY, self.cid, dumps(daily_info))

        # 副本全扫荡 dungeon battle奖励金币、仙魂、经验
        battle_count = 0  # 扫荡副本的次数
        drop_items   = [] # [[type, id, num], ...]
        dungeon_info = [] # 副本的怪物组挑战次数信息
        exp_reward, soul_reward, golds_reward = 0, 0, 0
        for d_id, d_count in left_dungeon_ids:
            dungeon = yield self.get_dungeon( scene_id, d_id )
            if not dungeon:
                log.error('Unknown dungeon id. cid: {0}, scene_id: {1}, dungeon_id: {2}.'.format( self.cid, scene_id, d_id ))
                continue
            dungeon.dungeon_today_count += d_count
            dungeon.dungeon_last_time    = datetime.now()
            dungeon_info.append( (d_id, dungeon.dungeon_today_count) )
            # 怪物组conf
            monster_conf = get_monster_conf( d_id, scene_conf['SceneDiff'] )
            if not monster_conf:
                log.error('Can not find monster conf. cid: {0}, dungeon_id: {1}.'.format( self.cid, d_id ))
                continue
            # 累计副本战斗次数
            battle_count += d_count
            for _c in range(0, d_count):
                tmp_golds, tmp_soul, tmp_exp, no_energy = 0, 0, 0, False
                if self.user.base_att.energy >= 5:
                    self.user.base_att.energy -= 5
                    tmp_exp = self.user.base_att.level * BATTLE_MONSTER_EXP_RATIO
                else:
                    no_energy = True
                    tmp_exp = self.user.base_att.level
                tmp_soul    = monster_conf['Soul']
                tmp_golds   = monster_conf['Money']

                # 获取怪物组掉落
                tmp_drop = yield self.dungeon_star_drop( d_id, scene_conf['SceneDiff'], no_energy )
                for _t in tmp_drop:
                    drop_items = add_new_items(_t, drop_items)
                # 发放奖励, 判断是否升级
                yield self.user.update_battle_attr( tmp_soul, tmp_golds, tmp_exp, way_type=WAY_SCENE_ALL_SWEEP )
                exp_reward   += tmp_exp
                soul_reward  += tmp_soul
                golds_reward += tmp_golds
        # 掉落发放到领奖中心
        if drop_items:
            timestamp = int(time())
            yield g_AwardCenterMgr.new_award( self.cid, AWARD_TYPE_SCENE_SWEEP, [timestamp, scene_id, drop_items] )

        # 每日任务计数
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_3, battle_count )
        # add syslog
 
        defer.returnValue( (dungeon_info, (golds_reward, soul_reward, exp_reward), self.user.base_att.credits, self.user.base_att.energy, items_return) )

    @defer.inlineCallbacks
    def ranklist(self):
        ''' 剧情副本的排行榜 '''
        yield self._load()
        # get myself rank and star
        _my_rank   = yield redis.zrank(SET_SCENE_CID_STAR, self.cid)
        _my_rank   = 0 if _my_rank is None else int(_my_rank)+1
        _ranklist  = [self.total_star, _my_rank, []]

        _cid_stars = yield redis.zrange(SET_SCENE_CID_STAR, 0, 9, withscores=True)
        #log.error('For Test. _cid_stars: {0}.'.format( _cid_stars ))
        for _idx, _data in enumerate(_cid_stars):
            if int(_data[1]) >= 0:
                continue
            _detail = yield load_scene_user_data(_data[0])
            if not _detail:
                log.error('Unknown user. cid: {0}.'.format( _data[0] ))
                continue
            _detail.extend( [-int(_data[1]), _idx+1] )
            _ranklist[2].append( _detail )

        defer.returnValue( _ranklist )

    @defer.inlineCallbacks
    def get_scene_reset_daily(self):
        ''' 获取玩家当天已全扫荡的次数、道具重置的次数、钻石重置的次数 '''
        reset_data = yield redis.hget(HASH_SCENE_RESET_DAILY, self.cid)
        if reset_data:
            reset_data = loads(reset_data)
            # 0-diff date, 1-same today
            if 1 == timestamp_is_today(reset_data[0]):
                defer.returnValue( reset_data )

        defer.returnValue( [int(time()), 0, 0, 0] )

    @defer.inlineCallbacks
    def reset_dungeon_count(self, scene_id, dungeon_id, reset_way):
        dungeon = yield self.get_dungeon(scene_id, dungeon_id)
        if not dungeon:
            log.error('Unknown dungeon id. scene_id: {0}, dungeon_id: {1}.'.format( scene_id, dungeon_id ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        # 判断是否还有剩余挑战次数
        #if 1 > dungeon.dungeon_today_count:
        #    defer.returnValue( REQUEST_LIMIT_ERROR )

        daily_info = yield self.get_scene_reset_daily()
        had_reset  = daily_info[2] + daily_info[3]
        # 检查当天最大可重置次数
        vip_conf = get_vip_conf( self.user.vip_level )
        if not vip_conf or (had_reset >= vip_conf['DungeonReset']):
            log.error('Dungeon reset count limit. cid:{0}, vip_level:{1}, max_count:{2}, item_reset:{3}, credit_reset:{4}.'.format( \
                    self.cid, self.user.vip_level, vip_conf['DungeonReset'] if vip_conf else 0, daily_info[2], daily_info[3]))
            defer.returnValue( CHAR_VIP_LEVEL_LIMIT )

        items_return = []
        # 检查reset_way
        if reset_way == SCENE_RESET_ITEM:
            daily_info[2] += 1
            # 扣道具 
            total_item, item_attribs = yield self.user.bag_item_mgr.get_items( ITEM_SCENE_RESET_ID )
            if 1 > total_item:
                defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            res_err, used_attribs = yield self.user.bag_item_mgr.use(ITEM_SCENE_RESET_ID, 1)
            if res_err:
                defer.returnValue( res_err )
            # used_attribs-已使用的道具
            for _a in used_attribs:
                items_return.append( [_a.attrib_id, ITEM_TYPE_ITEM, ITEM_SCENE_RESET_ID, _a.item_num] )
                # add syslog
                syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, \
                        self.user.alliance_id, _a.attrib_id, ITEM_SCENE_RESET_ID, 1, WAY_SCENE_RESET)
        elif reset_way == SCENE_RESET_CREDIT:
            daily_info[3] += 1
            # 扣钻石
            need_credits = get_scene_reset_conf(daily_info[3])
            if 0 == need_credits:
                defer.returnValue( SCENE_RESET_ERROR )
            if need_credits > self.user.credits:
                log.error('credits not enough. cid:{0}, need:{1}, curr:{2}, credit_reset:{3}.'.format( self.cid, need_credits, self.user.credits, daily_info[3] ))
                defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
            yield self.user.consume_credits( need_credits, WAY_SCENE_RESET )
        else:
            log.error('Unknown args. cid: {0}, reset_way: {1}.'.format( self.cid, reset_way ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        dungeon.dungeon_today_count = 0

        yield redis.hset(HASH_SCENE_RESET_DAILY, self.cid, dumps(daily_info))

        # 删除redis冷却时间记录
        yield redis.hdel( HASH_SCENE_COOLDOWN_TIME, self.cid )

        defer.returnValue( (self.user.credits, items_return) )



