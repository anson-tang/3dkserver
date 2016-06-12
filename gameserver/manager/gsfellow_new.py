#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time     import time
from log      import log
from errorno  import *
from constant import *
from marshal  import loads, dumps
from utils    import datetime2string, split_items
from system   import get_fellow_by_fid, get_roleexp_by_level, get_fellow_advanced, get_character_by_leadid
from syslogger import syslogger

from twisted.internet       import defer
from protocol_manager       import cs_call, gw_broadcast
from manager.gsattribute    import GSAttribute

class GSFellowMgr(object):
    _table = 'fellow'

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid
        self.__gsattribs  = None
        # 主角fellow
        self.__major_ufid = None
        # 布阵后的阵型, list下标对应阵型位置ID, 范围1-6, 值对应user_fellow_id
        self.__formation  = [0, 0, 0, 0, 0, 0]
        # 阵容, list下标对应阵容位置ID, 范围1-6, 值对应user_fellow_id
        self.__camp       = [0, 0, 0, 0, 0, 0]
        # 阵容羁绊
        self.__predestine = [0, 0, 0, 0, 0, 0]

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def value(self, attrib_id):
        yield self._load()
        attrib = self.__gsattribs.get( attrib_id, None )
        if not attrib:
            defer.returnValue( [] )
        defer.returnValue( [attrib.attrib_id, attrib.fellow_id, attrib.level, attrib.exp, attrib.advanced_level, attrib.on_troop, attrib.camp_id] )

    @defer.inlineCallbacks
    def _load(self):
        if self.__gsattribs is None:
            if not self.__loading:
                self.__loading = True
                #log.info('For Test. load. self.__gsattribs is None.')
                self.__gsattribs = yield GSAttribute.load( self.cid, GSFellowMgr._table )
                for attrib in self.__gsattribs.itervalues():
                    self.initialize( attrib )

                for d in self.__defers:
                    d.callback(True)

                self.__loading = False
                self.__defers  = []
            else:
                d = defer.Deferred()
                self.__defers.append(d)
                yield d

    def initialize(self, attrib):
        # 主角fellow
        if attrib.is_major > 0:
            attrib.level = self.user.base_att.level
            if self.__major_ufid is None:
                self.__major_ufid = attrib.attrib_id
            else:
                log.error('Duplicate major! cid:{0}, major ufid: {1}, ufid: {2}'.format( self.cid, self.__major_ufid, attrib.attrib_id ))
        # 阵型中的fellow
        if attrib.camp_id > 0:
            # 布阵信息
            if attrib.on_troop > 0 and attrib.on_troop < 7:
                if attrib.is_major > 0:
                    self.__formation[attrib.on_troop-1] = attrib.attrib_id
                    self.__camp[attrib.camp_id-1] = attrib.attrib_id
                else: # 检查错误数据
                    if self.__camp[attrib.camp_id-1]:
                        log.error('Duplicate fellow camp data. cid: {0}, camp_id: {1}, old_ufid: {2}, ufid: {3}.'.format( self.cid, attrib.camp_id, self.__camp[attrib.camp_id-1], attrib.attrib_id ))
                        attrib.on_troop = 0
                        attrib.camp_id  = 0
                    else:
                        if self.__formation[attrib.on_troop-1]:
                            log.error('Duplicate fellow formation data. cid: {0}, on_troop: {1}, old_ufid: {2}, ufid: {3}.'.format( self.cid, attrib.on_troop, self.__formation[attrib.on_troop-1], attrib.attrib_id ))
                            attrib.on_troop = 0
                            attrib.camp_id  = 0
                        else:
                            self.__formation[attrib.on_troop-1] = attrib.attrib_id
                            self.__camp[attrib.camp_id-1] = attrib.attrib_id
            else: # 重置阵容信息
                attrib.on_troop = 0
                attrib.camp_id  = 0
        # 不在阵型中fellow的on_troop一定不可能属于1-6直接
        elif attrib.on_troop > 0 and attrib.on_troop < 7:
            log.error('Duplicate fellow formation error. cid: {0}, on_troop: {1}, ufid: {2}.'.format( self.cid, attrib.on_troop, attrib.attrib_id ))
            attrib.on_troop = 0

        # 羁绊小伙伴中的fellow
        if attrib.on_troop > 6:
            # 羁绊小伙伴的camp_id一定等于0
            if attrib.camp_id != 0:
                log.error('Duplicate fellow camp error. cid: {0}, ufid: {1}.'.format( self.cid, attrib.attrib_id ))
                attrib.camp_id = 0
            # 检查羁绊阵容中该位置上是否已有fellow
            if self.__predestine[attrib.on_troop-6-1]:
                log.error('Duplicate fellow predestine data! cid: {0}, old ufid: {1}, ufid: {2}.'.format( self.cid, self.__predestine[attrib.on_troop-6-1], attrib.attrib_id ))
                attrib.on_troop = 0
            else:
                self.__predestine[attrib.on_troop-6-1] = attrib.attrib_id

    def sync_to_cs(self):
        if self.__gsattribs:
            for attrib in self.__gsattribs.itervalues():
                attrib.syncToCS()

    def get_null_formation_id(self):
        ''' 获取阵型中的空位, 无阵型解锁 '''
        for _idx in FELLOW_FORMATION_ORDER:
            if not self.__formation[_idx]:
                return _idx + 1
        return 0

    def get_formation_id(self, user_fellow_id):
        ''' get formation fellow id by user_fellow_id '''
        for _idx, _ufid in enumerate( self.__formation ):
            if _ufid == user_fellow_id:
                return _idx + 1
        return 0

    def get_fellow(self, user_fellow_id):
        return self.__gsattribs.get(user_fellow_id, None)

    @defer.inlineCallbacks
    def cur_capacity(self):
        yield self._load()
        count = 0
        # 已上阵的伙伴不计算在伙伴背包内
        for attrib in self.__gsattribs.itervalues():
            if attrib.on_troop == 0:
                count += 1
        defer.returnValue( count )

    def get_fellows_by_fid(self, fellow_id, user_fellow_id=0):
        '''
        @summary: 获取fellow list中所有与fellow id相同的attrib
        '''
        total_num, fellow_attribs = 0, []
        for attrib in self.__gsattribs.itervalues():
            if attrib.fellow_id == fellow_id:
                if attrib.attrib_id == user_fellow_id:
                    continue
                if attrib.deleted > 0:
                    log.error('Dirty fellow data. ufid: {0}.'.format( attrib.attrib_id ))
                    continue
                total_num += 1
                fellow_attribs.append( attrib )

        return total_num, fellow_attribs

    @property
    @defer.inlineCallbacks
    def ids_green(self):
        yield self._load()

        ids = []
        for attrib in self.__gsattribs.itervalues():
            if attrib.is_major or attrib.on_troop or attrib.camp_id or attrib.advanced_level:
                continue

            _conf = get_fellow_by_fid(attrib.fellow_id)

            if _conf['Quality'] <= QUALITY_GREEN:
                ids.append(attrib.attrib_id)

        defer.returnValue(ids)

    @property
    @defer.inlineCallbacks
    def value_list(self):
        yield self._load()
        count = 0
        value_list   = []
        max_capacity = self.user.base_att.fellow_capacity
        major_value  = yield self.value(  self.__major_ufid )
        # 主角是第一个元素
        if not major_value:
            log.error('Can not find the major fellow. major_ufid: {0}, all_fellow_ids: {1}.'.format( self.__major_ufid, self.__gsattribs.keys() ))
            defer.returnValue( CHAR_DATA_ERROR )
        else:
            value_list = [major_value]
            if major_value[0] not in self.__formation:
                log.error('Major not in user formation.')

        for attrib in self.__gsattribs.itervalues():
            # 主角fellow
            if attrib.is_major > 0:
                continue
            if attrib.camp_id > 0 and (attrib.attrib_id not in self.__formation):
                log.error('Fellow in camp but not in formation. ufid: {0}.'.format( attrib.attrib_id ))
                # 按照一定顺序添加进formation
                _null_formation_id = self.get_null_formation_id()
                if _null_formation_id > 0:
                    self.__formation[_null_formation_id-1] = attrib.attrib_id
                    attrib.on_troop = _null_formation_id
                else: # 阵型中没有空位置时把它重置
                    attrib.camp_id = 0
            # 已上阵的伙伴含羁绊不计算在伙伴背包内
            if attrib.on_troop == 0:
                count += 1

            value_list.append( (attrib.attrib_id, attrib.fellow_id, attrib.level, attrib.exp, attrib.advanced_level, attrib.on_troop, attrib.camp_id) )

        defer.returnValue( (count, max_capacity, value_list) )

    @defer.inlineCallbacks
    def create_table_data(self, fellow_id, is_major, camp_id, on_troop, way_type=WAY_UNKNOWN, way_others=''):
        yield self._load()

        time_now = int(time()) #datetime2string()
        gsattrib = GSAttribute( self.cid, GSFellowMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, fellow_id=fellow_id, level=1, exp=0, advanced_level=0, on_troop=on_troop, is_major=is_major, camp_id=camp_id, deleted=0, create_time=time_now, update_time=time_now, del_time=0)
        if res_err:
            log.error('GSBagEquipMgr create table data error. res_err: {0}.'.format( res_err ))
            defer.returnValue( (UNKNOWN_ERROR, None) )

        self.__gsattribs[gsattrib.attrib_id] = gsattrib
        # 创建玩家角色时初始化阵容等信息
        if is_major:
            self.initialize( gsattrib )

        conf = get_fellow_by_fid( fellow_id )
        if conf:
            # 判断图鉴
            yield self.user.atlaslist_mgr.new_atlaslist(CATEGORY_TYPE_FELLOW, conf['Camp'], conf['Quality'], fellow_id)
            if conf['Quality'] >= QUALITY_PURPLE:
                yield self.user.goodwill_mgr.create_table_data( fellow_id )
            # add syslog
            syslogger(LOG_FELLOW_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, gsattrib.attrib_id, fellow_id, conf['QualityLevel'], conf['Star'], way_type, way_others)
        defer.returnValue( (NO_ERROR, gsattrib) )

    def delete_table_data(self, attrib_id):
        '''
        @summary: 修改标志位deleted=1, 更新self.__gsattribs
        '''
        #log.info('For Test. delete fellow. attrib_id: {0}.'.format( attrib_id ))
        if self.__gsattribs.has_key( attrib_id ):
            gsattrib = self.__gsattribs[attrib_id]
            gsattrib.delete()
            del self.__gsattribs[attrib_id]
        else:
            log.error('Can not find delete data. ufid: {0}.'.format( attrib_id ))

    def check_camp_fellow(self, fellow_id, camp_id):
        '''
        @summary: 检查是否有相同的fellow_id已上阵
        '''
        for _c_id, _ufid in enumerate(self.__camp):
            if _c_id == camp_id:
                continue
            attrib = self.__gsattribs.get( _ufid, None )
            if attrib and fellow_id == attrib.fellow_id:
                return True

        for _ufid in self.__predestine:
            attrib = self.__gsattribs.get( _ufid, None )
            if attrib and fellow_id == attrib.fellow_id:
                return True

        return False

    @defer.inlineCallbacks
    def get_formation(self):
        yield self._load()
        defer.returnValue( self.__formation )

    @defer.inlineCallbacks
    def get_offline_formation(self):
        ''' 获取对手的阵型中的fellow_id '''
        yield self._load()
        _fids = []
        for _ufid in self.__formation:
            attrib = self.__gsattribs.get( _ufid, None )
            if attrib:
                if attrib.is_major > 0:
                    _fids.append( self.user.base_att.lead_id )
                else:
                    _fids.append( attrib.fellow_id )

        defer.returnValue( _fids )

    @defer.inlineCallbacks
    def set_formation(self, list_formation):
        ''' 玩家布阵 '''
        yield self._load()
        if len(list_formation) != len(self.__formation):
            log.error('formation data length error.')
            defer.returnValue( CLIENT_DATA_ERROR )

        for _idx, _ufid in enumerate(list_formation):
            if _ufid == 0:
                continue
            attrib = self.__gsattribs.get( _ufid, None )
            if not attrib:
                log.error('Unknown user fellow id. ufid: {0}.'.format( _ufid ))
                defer.returnValue( UNKNOWN_FELLOW_ERROR )

            attrib.on_troop = _idx + 1

        self.__formation = list_formation
        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def strengthen_by_card(self, user_fellow_id, upgrade_info):
        '''
        @summary: fellow强化 紫品、已上阵的不能用于强化升级，经验可累积
        '''
        yield self._load()
        if len(upgrade_info) < 1 or len(upgrade_info) > 5:
            log.error('Strengthened fellow count error.')
            defer.returnValue( CLIENT_DATA_ERROR )

        attrib = self.__gsattribs.get( user_fellow_id, None )
        if not attrib:
            log.error('Unknown user fellow id. ufid: {0}.'.format( user_fellow_id ))
            defer.returnValue( UNKNOWN_FELLOW_ERROR )
        conf = get_fellow_by_fid( attrib.fellow_id )
        if not conf:
            log.error('Can not find the conf. fellow_id: {0}.'.format( attrib.fellow_id ))
            defer.returnValue( NOT_FOUND_CONF )
        if 1 == attrib.is_major or attrib.level >= self.user.base_att.level:
            log.error('Can not strengthen major fellow or max level limit.')
            defer.returnValue( LEVEL_UPGRADE_TARGET_INVALID )

        total_add_exp = 0
        used_ufids    = [] # 实际用于强化的user_fellow_id列表
        for _ufid in upgrade_info:
            used_attrib = self.__gsattribs.get( _ufid, None )
            if not used_attrib:
                log.error('Unknown user fellow id. ufid: {0}.'.format( _ufid ))
                defer.returnValue( UNKNOWN_FELLOW_ERROR )
            # 已上阵或主角不可作为强化的材料
            if used_attrib.on_troop > 0 or used_attrib.is_major > 0:
                log.error('Can not use the fellow to strengthen. _ufid: {0}.'.format( _ufid ))
                defer.returnValue( REQUEST_LIMIT_ERROR )
            used_conf = get_fellow_by_fid( used_attrib.fellow_id )
            if not used_conf:
                log.error('Can not find the conf. fellow_id: {0}.'.format( used_attrib.fellow_id ))
                defer.returnValue( NOT_FOUND_CONF )
            # 紫品不可作为强化的材料
            if QUALITY_PURPLE == used_conf['Quality']:
                log.error('Can not use purple fellow to strengthen. _ufid: {0}.'.format( _ufid ))
                defer.returnValue( REQUEST_LIMIT_ERROR )
            #log.info('For Test. total_add_exp: {0}.'.format( total_add_exp ))
            total_add_exp += (used_conf['Exp'] + used_attrib.exp)
            for _level in range(used_conf['Level'], used_attrib.level):
                _roleexp_conf = get_roleexp_by_level( _level )
                _level_exp = _roleexp_conf.get( FELLOW_QUALITY[used_conf['Quality']], 0 )
                #log.info('For Test. total_add_exp: {0}, _level_exp: {1}, _level: {2}, _quality: {3}.'.format( total_add_exp, _level_exp, _level, used_conf['Quality'] ))
                if _level_exp:
                    total_add_exp += _level_exp
            used_ufids.append( _ufid )
 
        consume_golds  = total_add_exp # 1 exp = 1 golds
        if consume_golds > self.user.base_att.golds:
            log.error('Strengthened need golds: {0}, cur golds: {1}.'.format( consume_golds, self.user.base_att.golds ))
            defer.returnValue( CHAR_GOLD_NOT_ENOUGH )
 
        # 扣金币
        #self.user.base_att.golds -= consume_golds
        self.user.consume_golds( consume_golds, WAY_FELLOW_STRENGTHEN )
        # 删除作为材料的fellow
        for _ufid in used_ufids:
            self.delete_table_data( _ufid )
            #used_attrib.delete()

        # 计算升级后的等级和经验
        total_add_exp += attrib.exp
        final_level, final_exp = self.cal_level_upgrade(self.user.base_att.level, conf['Quality'], total_add_exp, attrib.level)
        if final_level != attrib.level:
            syslogger(LOG_FELLOW_STRENGTHEN, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_fellow_id, \
                    attrib.fellow_id, attrib.level, final_level, WAY_FELLOW_STRENGTHEN, str(tuple(used_ufids)))
            attrib.level = final_level
            # 已上阵的伙伴或主角强化 同步camp到redis
            #if attrib.on_troop > 0 or attrib.is_major > 0:
            #    yield self.user.sync_camp_to_redis(update=True)

        if final_exp != attrib.exp:
            attrib.exp   = final_exp
        #成就
        yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_28, attrib.level)

        defer.returnValue( [user_fellow_id, attrib.fellow_id, attrib.level, attrib.exp, self.user.base_att.golds, self.user.base_att.soul] )

    def cal_level_upgrade(self, max_level, quality, total_add_exp, cur_level):
        '''
        @summary: 读取角色升级配置, 根据总经验值和现有经验, 计算伙伴强化后的等级和经验
        @param  : max_level-伙伴可强化的最高等级，quality-伙伴的品质，total_add_exp-总经验值
        '''
        final_level = cur_level # 初始值
        while total_add_exp > 0:
            _roleexp_conf = get_roleexp_by_level( final_level )
            _need_exp     = _roleexp_conf.get( FELLOW_QUALITY[quality], 0 )
            #log.info('For Test. total_add_exp: {0}, _need_exp: {1}, quality: {2}.'.format( total_add_exp, _need_exp, quality ))
            if not _need_exp:
                log.error("Can not find the roleexp's conf. final_level: {0}.".format( final_level+1 ))
                break
            # 伙伴等级升级时所需经验不足
            if (total_add_exp - _need_exp) < 0:
                break
            # 伙伴的等级已超过玩家的等级
            if final_level >= max_level:
                break
            total_add_exp -= _need_exp
            final_level   += 1
 
        return final_level, total_add_exp

    @defer.inlineCallbacks
    def strengthen_by_soul(self, user_fellow_id, upgrade_info):
        ''' 
        @summary: 仙魂强化 1仙魂=1经验，扣1金币
        @param  : upgrade_soul_type-1:仙魂普通强化; 2:仙魂自动强化
        '''
        yield self._load()
        [ upgrade_soul_type ] = upgrade_info

        attrib = self.__gsattribs.get( user_fellow_id, None )
        if not attrib:
            log.error('Unknown user fellow id. ufid: {0}.'.format( user_fellow_id ))
            defer.returnValue( UNKNOWN_FELLOW_ERROR )

        conf = get_fellow_by_fid( attrib.fellow_id )
        if not conf:
            log.error('Can not find the conf. fellow_id: {0}.'.format( attrib.fellow_id ))
            defer.returnValue( NOT_FOUND_CONF )

        last_level, last_exp = attrib.level, attrib.exp
        user_soul, user_golds, user_level = self.user.base_att.soul, self.user.base_att.golds, self.user.base_att.level

        _count = 1
        _flag  = True
        while _flag:
            _roleexp_conf = get_roleexp_by_level( last_level )
            _need_exp     = _roleexp_conf.get( FELLOW_QUALITY[conf['Quality']], 0 )
            if not _need_exp:
                log.error("Can not find the roleexp's conf. cur_level: {0}.".format( attrib.level ))
                defer.returnValue( NOT_FOUND_CONF )

            _need_soul    = (_need_exp - last_exp) if (last_exp < _need_exp) else 0
            if _count == 1: # 第一次条件不满足时, 返回错误
                if (user_soul < _need_soul):
                    defer.returnValue( CHAR_SOUL_NOT_ENOUGH )
                if (user_golds < _need_soul):
                    defer.returnValue( CHAR_GOLD_NOT_ENOUGH )
                if (user_level <= last_level):
                    defer.returnValue( CHAR_LEVEL_LIMIT )
            # 仙魂不足, 金币不足, 等级已到上限
            if (user_soul < _need_soul) or (user_golds < _need_soul) or (user_level <= last_level):
                break
            _count     += 1
            last_level += 1
            last_exp    = 0 if (last_exp < _need_exp) else (last_exp - _need_exp)

            user_soul   -= _need_soul
            user_golds  -= _need_soul
            if 1 == upgrade_soul_type: # 普通强化
                _flag = False

        syslogger(LOG_FELLOW_STRENGTHEN, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_fellow_id, \
                attrib.fellow_id, attrib.level, last_level, WAY_FELLOW_SOUL_STRENGTHEN, str((self.user.base_att.soul - user_soul)))
        # 升级等级
        attrib.level, attrib.exp = last_level, last_exp
        # 已上阵的伙伴或主角强化 同步camp到redis
        #if attrib.on_troop > 0 or attrib.is_major > 0:
        #    yield self.user.sync_camp_to_redis(update=True)

        # 扣仙魂、金币
        self.user.base_att.soul  = user_soul
        #self.user.base_att.golds = user_golds
        if user_golds != self.user.base_att.golds:
            self.user.consume_golds( self.user.base_att.golds-user_golds, WAY_FELLOW_SOUL_STRENGTHEN )
 
        defer.returnValue( [user_fellow_id, attrib.fellow_id, attrib.level, attrib.exp, self.user.base_att.golds, self.user.base_att.soul] )

    @defer.inlineCallbacks
    def advanced(self, user_fellow_id):
        ''' 伙伴进阶 '''
        attrib = self.__gsattribs.get( user_fellow_id, None )
        if not attrib:
            log.error('Unknown user fellow id. ufid: {0}.'.format( user_fellow_id ))
            defer.returnValue( UNKNOWN_FELLOW_ERROR )

        # 主角进阶时取sysconfig['character']的config
        if attrib.is_major > 0:
            conf      = get_character_by_leadid( self.user.base_att.lead_id )
            fellow_id = self.user.base_att.lead_id
            attrib.level = self.user.base_att.level
        else:
            conf      = get_fellow_by_fid( attrib.fellow_id )
            fellow_id = attrib.fellow_id

        if not conf:
            log.error('Can not find the conf. ufid: {0}.'.format( user_fellow_id ))
            defer.returnValue( NOT_FOUND_CONF )

        # 可进阶次数限制
        if attrib.advanced_level >= conf['AdvancedCount']:
            log.error('Fellow advanced count limit. max count: {0}.'.format( conf['AdvancedCount'] ))
            defer.returnValue( ADVANCED_MAX_COUNT )

        advanced_conf = get_fellow_advanced( fellow_id, attrib.advanced_level+1 )
        if not advanced_conf:
            log.error('Can not find advanced conf. user_fellow_id: {0}.'.format( user_fellow_id ))
            defer.returnValue( NOT_FOUND_CONF )
        # 进阶时的伙伴等级限制
        if advanced_conf['FellowLevelLimit'] > attrib.level:
            log.error('fellow level limit. user_fellow_id: {0}, need >= {1}, cur: {2}.'.format( user_fellow_id, advanced_conf['FellowLevelLimit'], attrib.level ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 金币不足
        if advanced_conf['Gold'] > self.user.base_att.golds:
            log.error('Advanced need golds: {0}, cur golds: {1}.'.format( advanced_conf['Gold'], self.user.base_att.golds ))
            defer.returnValue( CHAR_GOLD_NOT_ENOUGH )
        # 进阶消耗的道具不足, 含消耗伙伴
        items_list = split_items( advanced_conf['ItemList'] )
        for _type, _id, _num in items_list:
            if _type == ITEM_TYPE_ITEM:
                total_num, item_attribs = yield self.user.bag_item_mgr.get_items( _id )
                if _num > total_num:
                    log.error('item id: {0}, need num: {1}, cur num: {2}.'.format( _id, _num, total_num ))
                    defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            elif _type == ITEM_TYPE_FELLOW:
                total_num, _ = self.get_fellows_by_fid( _id, user_fellow_id )
                if _num > total_num:
                    log.error('Item id: {0}, need num: {1}, cur_num: {2}.'.format( _id, _num, total_num ))
                    defer.returnValue( FELLOW_NOT_ENOUGH )
            else:
                log.error('Unknown advanced item. item: {0}.'.format( (_type, _id, _num) ))
                defer.returnValue( UNKNOWN_ITEM_ERROR )

        # 扣金币、扣道具
        #self.user.base_att.golds -= advanced_conf['Gold']
        self.user.consume_golds( advanced_conf['Gold'], WAY_FELLOW_REFINE )
        items_return = []
        for _type, _id, _num in items_list:
            if _type == ITEM_TYPE_ITEM:
                res_err, used_attribs = yield self.user.bag_item_mgr.use( _id, _num )
                if res_err:
                    log.error('Use item error.')
                    defer.returnValue( res_err )
                # used_attribs-已使用的道具
                for _a in used_attribs:
                    items_return.append( [_a.attrib_id, _type, _id, _a.item_num] )
            elif _type == ITEM_TYPE_FELLOW:
                total_num, used_attribs = self.get_fellows_by_fid( _id, user_fellow_id )
                for _a in used_attribs[:_num]:
                    self.delete_table_data( _a.attrib_id )
                    items_return.append( [_a.attrib_id, _type, _id, 0] )
        # add syslog
        syslogger(LOG_FELLOW_REFINE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, user_fellow_id, \
                attrib.fellow_id, attrib.advanced_level, attrib.advanced_level+1, '')

        # 进阶后的属性提高
        attrib.advanced_level += 1

        # 已上阵的伙伴或主角强化 同步camp到redis
        #if attrib.on_troop > 0 or attrib.is_major > 0:
        #    yield self.user.sync_camp_to_redis(update=True)

        # 走马灯的成就广播之神将进阶到+5以上, 神将不含主角
        if (attrib.advanced_level > 4):
            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_ADVANCED, [self.user.base_att.nick_name, attrib.fellow_id, attrib.advanced_level]]]
            gw_broadcast('sync_broadcast', [message])
 
        defer.returnValue( (user_fellow_id, attrib.advanced_level, self.user.base_att.golds, items_return) )

    @defer.inlineCallbacks
    def set_camp_fellow(self, camp_id, old_ufid, new_ufid):
        '''
        @summary: 指定某fellow上阵, 替换阵容和阵型
        '''
        yield self._load()
        # 检查参数的合法性
        new_attrib = self.__gsattribs.get( new_ufid, None )
        if not new_attrib:
            log.error('Unknown user fellow id. new_ufid: {0}.'.format( new_ufid ))
            defer.returnValue( UNKNOWN_FELLOW_ERROR )

        # 检查参数的合法性
        old_attrib = None
        if old_ufid:
            old_attrib = self.__gsattribs.get( old_ufid, None )
            if not old_attrib:
                log.error('Unknown user fellow id. new_ufid: {0}.'.format( new_ufid ))
                defer.returnValue( UNKNOWN_FELLOW_ERROR )
            # 判断数据是否同步
            if old_ufid != self.__camp[camp_id-1]:
                log.error('Camp data error.')
                defer.returnValue( UNKNOWN_ERROR )
            # 主角不可替换
            if old_attrib.is_major > 0:
                log.error('Major could not be replace. old_ufid: {0}.'.format( old_ufid ))
                defer.returnValue( FELLOW_MAJOR_REPLACE_ERROR )

        # 未实现, 判断玩家的等级对应的可上阵fellow个数

        # 主角不可替换
        if new_attrib.is_major > 0:
            log.error('Major could not be replace. new_user_fellow_id: {0}.'.format( new_ufid ))
            defer.returnValue( FELLOW_MAJOR_REPLACE_ERROR )
        # 相同fellow 不可同时上阵
        camped_flag = self.check_camp_fellow( new_attrib.fellow_id, camp_id-1 )
        if camped_flag:
            log.error('Common fellow in camp.')
            defer.returnValue( FELLOW_COMMON_ON_TROOP )

        _old_formation_id = 0
        if old_attrib:
            _old_formation_id   = self.get_formation_id( old_ufid )
            # 还原camp、on_troop为初始值
            old_attrib.camp_id  = 0
            old_attrib.on_troop = 0

        # 更新阵型 fellow
        if _old_formation_id == 0 and (new_ufid not in self.__formation):
            _null_formation_id = self.get_null_formation_id()
            # 有空位且 该ufid不在阵型中
            #log.info('For Test. new_ufid: {0}, __formation: {1}.'.format( new_ufid, self.__formation ))
            if _null_formation_id > 0:
                self.__formation[_null_formation_id-1] = new_ufid
                new_attrib.on_troop = _null_formation_id
        else:
            self.__formation[_old_formation_id-1] = new_ufid
            new_attrib.on_troop = _old_formation_id

        # 更新阵容 fellow
        self.__camp[camp_id-1] = new_ufid
        new_attrib.camp_id      = camp_id

        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)
        #成就
        num = 0
        f = lambda x:x!=0
        num = len(filter(f, self.__camp)) + len(filter(f, self.__predestine))
        yield self.user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_22, num )
        defer.returnValue( NO_ERROR )


    def get_camp_fellow(self):
        '''
        @summary: 获取玩家的阵容
        '''
        return self.__camp

    @defer.inlineCallbacks
    def get_camp_fellow_id(self):
        ''' 竞技场中获取玩家阵容的伙伴ID ''' 
        yield self._load()
        fellow_ids = []
        for _ufid in self.__camp:
            attrib = self.__gsattribs.get(_ufid, None)
            if attrib:
                if attrib.is_major > 0:
                    fellow_ids.append( self.user.base_att.lead_id )
                else:
                    fellow_ids.append( attrib.fellow_id )
 
        defer.returnValue( fellow_ids )

    @defer.inlineCallbacks
    def set_camp_predestine(self, camp_pos_id, old_ufid, new_ufid):
        '''
        @summary: 设置上阵小伙伴的羁绊, 包含新增、替换、卸下
        '''
        yield self._load()
        # 检查参数是否有效, old_ufid 和 new_ufid 不能同时为空
        if camp_pos_id > len(self.__predestine) or not(old_ufid or new_ufid):
            log.error('Unknown pos_id: {0}, old_ufid: {1}, new_ufid: {1}.'.format( camp_pos_id, old_ufid, new_ufid ))
            defer.returnValue( CLIENT_DATA_ERROR )

        # 处理替换时的异常
        if not old_ufid and new_ufid and self.__predestine[camp_pos_id-1]:
            old_ufid = self.__predestine[camp_pos_id-1]

        if old_ufid:
            old_attrib = self.__gsattribs.get( old_ufid, None )
            if not old_attrib or (old_attrib.camp_id > 0):
                log.error('Unknown user fellow id or invalid fellow. ufid: {0}.'.format( old_ufid ))
                defer.returnValue( UNKNOWN_FELLOW_ERROR )
            old_attrib
            # 判断数据是否正确
            if old_ufid != self.__predestine[camp_pos_id-1]:
                log.error('Camp predestine data error.')
                defer.returnValue( UNKNOWN_ERROR )
            old_attrib.on_troop = 0
            self.__predestine[camp_pos_id-1] = 0


        if new_ufid:
            # 未知fellow id 或者 已上阵
            new_attrib = self.__gsattribs.get( new_ufid, None )
            if not new_attrib or (new_attrib.camp_id > 0):
                log.error('Unknown user fellow id or invalid fellow. ufid: {0}.'.format( new_ufid ))
                defer.returnValue( UNKNOWN_FELLOW_ERROR )
            self.__predestine[camp_pos_id-1] = new_ufid
            new_attrib.on_troop = camp_pos_id + 6

        # 同步camp到redis
        #yield self.user.sync_camp_to_redis(update=True)

        defer.returnValue( NO_ERROR )

    def get_camp_predestine(self):
        '''
        @summary: 返回上阵小伙伴的羁绊
        '''
        return self.__predestine

    def get_camp_predestine_fid(self):
        ''' 竞技场中获取玩家羁绊阵容的伙伴ID ''' 
        fellow_ids = []
        for _ufid in self.__predestine:
            attrib = self.__gsattribs.get(_ufid, None)
            if attrib:
                fellow_ids.append( attrib.fellow_id )
            else:
                fellow_ids.append( 0 )
 
        return fellow_ids
 
    def gm_get_camp_fellow(self, ufid):
        _fellow = {}
        attrib = self.get_fellow( ufid )
        if not attrib:
            return _fellow

        _fellow['fellow_name'] = ''
        _fellow['user_fellow_id'] = ufid
        _fellow['advanced_level'] = attrib.advanced_level 
        if attrib.is_major > 0:
            _fellow['user_fellow_id'] = self.user.cid
            _fellow['fellow_id']      = self.user.lead_id
            _fellow['level']          = self.user.level
            _fellow['exp']            = self.user.base_att.exp
            _fellow['fellow_name']    = self.user.nick_name
        else:
            conf = get_fellow_by_fid( attrib.fellow_id )
            if conf:
                _fellow['fellow_name'] = conf['Name']
            _fellow['fellow_id'] = attrib.fellow_id
            _fellow['level']     = attrib.level
            _fellow['exp']       = attrib.exp

        return _fellow

    @defer.inlineCallbacks
    def gm_fellow_info(self):
        yield self._load()
        _fellow_info = []
        for attrib in self.__gsattribs.itervalues():
            _fellow_info.append( {'user_item_id':attrib.attrib_id, 'item_type':ITEM_TYPE_FELLOW, 'item_id':attrib.fellow_id, 'item_cnt':1, 'level':attrib.level, 'refine':[], 'exp':attrib.exp, 'refine_level':attrib.advanced_level} )

        defer.returnValue( _fellow_info )


