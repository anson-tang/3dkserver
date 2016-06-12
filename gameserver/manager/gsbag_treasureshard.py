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
from utils    import datetime2string
from redis    import redis

from syslogger              import syslogger
from twisted.internet       import defer
from system                 import get_item_by_itemid
from manager.gsattribute    import GSAttribute
from marshal import dumps, loads

class GSBagTreasureShardMgr(object):
    '''
    @summary: 玩家宝物碎片背包
    '''
    _table  = 'bag_treasureshard'

    def __init__(self, user):
        '''
        @param: __camp_position format: {camp_id: {position_id: user_treasure_id, ...}, ...}, 其中camp_id范围1-6, position_id范围是1-4
        '''
        self.user = user
        self.cid  = user.cid
        self.__gsattribs = None

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def _load(self):
        if self.__gsattribs is None:
            if not self.__loading:
                self.__loading = True
                self.__gsattribs = yield GSAttribute.load( self.cid, GSBagTreasureShardMgr._table )

                for d in self.__defers:
                    d.callback(True)

                self.__loading = False
                self.__defers  = []
            else:
                d = defer.Deferred()
                self.__defers.append(d)
                yield d

    def sync_to_cs(self):
        if self.__gsattribs:
            for attrib in self.__gsattribs.itervalues():
                attrib.syncToCS()

    @defer.inlineCallbacks
    def get_item_by_item_id(self, item_id):
        ''' __gsattribs中保存是按照规则排序后的数据
        '''
        yield self._load()
        for attrib in self.__gsattribs.itervalues():
            if attrib.item_id == item_id:
                defer.returnValue( attrib )
        defer.returnValue( None )

    @defer.inlineCallbacks
    def get(self, user_item_id):
        yield self._load()
        defer.returnValue( self.__gsattribs.get(user_item_id, None) )

    @defer.inlineCallbacks
    def value_list_by_type(self, shard_type):
        yield self._load()
        value_list = []
        for attrib in self.__gsattribs.itervalues():
            item_conf = get_item_by_itemid( attrib.item_id )

            if item_conf and item_conf['ItemType'] == shard_type:
                value_list.append( (attrib.attrib_id, attrib.item_id, attrib.item_num) )

        defer.returnValue( value_list )

    def add_new_items(self, new, items=[]):
        ''' new=[uid, type, id, num], 其中num为道具新增的数量 '''
        if not new or len(new) != 4:
            return items

        for _i in items:
            if _i[:3] == new[:3]:
                _i[3] += new[3]
                break
        else:
            items.append( new )

        return items

    @defer.inlineCallbacks
    def new(self, item_id, item_num, way_type=WAY_UNKNOWN, way_others=''):
        yield self._load()
        item_conf = get_item_by_itemid( item_id )
        if not item_conf:
            log.error('Can not find conf. item_id: {0}.'.format( item_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )
        # 检查道具类型
        item_type  = item_conf['ItemType']
        if item_type not in BAG_TREASURESHARD:
            log.error('new. Item type error. item_id: {0}.'.format( item_id ))
            defer.returnValue( (ITEM_TYPE_ERROR, None) )

        # 检查 item_num
        if item_num < 1:
            log.error('add item num error.')
            defer.returnValue( (UNKNOWN_ERROR, None) )

        time_now   = int(time()) #datetime2string()
        # 宝物碎片可以无限叠加
        #MAX_NUM    = item_conf['MaxOverlyingCount']
        new_items  = []
        for attrib in self.__gsattribs.itervalues():
            if item_type == attrib.item_type and item_id == attrib.item_id:
                attrib.item_num += item_num
                new_items = self.add_new_items( [attrib.attrib_id, item_type, item_id, item_num], new_items )
                break
        else:
            cur_item_num = item_num
            if cur_item_num > 0:
                res_err, new_attrib = yield self.create_table_data(item_type, item_id, cur_item_num, time_now)
                if res_err:
                    defer.returnValue( (UNKNOWN_ERROR, None) )
                new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, cur_item_num], new_items )

        # 碎片可合成的宝物信息
        _, treasure_id, _ = item_conf['ChangeList'][0]
        yield self.update_avoid_cache( treasure_id )

        # add syslog
        for _item in new_items:
            syslogger(LOG_ITEM_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _item[0], _item[2], _item[3], way_type, way_others)
        defer.returnValue( (NO_ERROR, new_items) )

    @defer.inlineCallbacks
    def update_avoid_cache(self, treasure_id):
        '''
        @summary: 维护宝物碎片列表的同时, 维护redis中的玩家阵营数据
        '''
        if self.user.base_att.level <= AVOID_WAR_LEVEL:
            log.warn('User level <= 12 could not be plunder. cid: {0}.'.format( self.cid ))
            defer.returnValue( REQUEST_LIMIT_ERROR )

        treasure_conf = get_item_by_itemid( treasure_id )
        if not treasure_conf:
            log.error('Can not find conf. treasure_id: {0}.'.format( treasure_id ))
            defer.returnValue( NOT_FOUND_CONF )
        _shard_list = [splited[1] for splited in treasure_conf['ChangeList'] ]

        # 只有同时拥有“一个宝物的2个或者2个以上，不同位置碎片”的玩家才会被加入被抢夺列表
        _haved = 0
        _plunder_list = [] # 可被抢夺的碎片
        for _shard_id in _shard_list:
            for attrib in self.__gsattribs.itervalues():
                if attrib.item_id == _shard_id:
                    _haved += 1
                    _plunder_list.append( _shard_id )
                    break

        #_treasure_ids = yield redis.hget( HASH_TREASURE_CHARACTER_IDS, self.cid )
        #if _treasure_ids:
        #    _treasure_ids = loads(_treasure_ids)
        #else:
        #    _treasure_ids = []

        #log.info('For Test. _haved: {0}, cid: {1}, _shard_id: {2}, _shard_list: {3}, _plunder_list: {4}.'.format( _haved, self.cid, _shard_id, _shard_list, _plunder_list ))
        for _shard_id in _shard_list:
            yield redis.hdel( TPL_TREASURE_SHARD_GOT % _shard_id, self.cid )

        #if treasure_id in _treasure_ids:
        #    _treasure_ids.remove( treasure_id )

        if _haved > 1:
            #_flag   = True  # 成功获取玩家有效阵容
            #_exists = yield redis.hexists( HASH_TREASURE_CHARACTER_CAMP, self.cid )
            #if (not _exists):
            #    _all_camps = yield self.user.get_camp()
            #    fellow_ids = []
            #    if _all_camps:
            #        for camp_data in _all_camps[1]:
            #            if not camp_data or not camp_data[1]:
            #                continue
            #            fellow_ids.append( camp_data[1][1] )

            #    # 有效的玩家阵容
            #    if fellow_ids:
            #        yield redis.hset( HASH_TREASURE_CHARACTER_CAMP, self.cid, dumps(_all_camps) )
            #        #log.info('For Test. save treasure camp. cid: {0}.'.format( self.cid ))
            #    else:
            #        _flag = False
            #        log.error('Save char treasure camp data fail. cid: {0}, _all_camps: {1}.'.format( self.cid, _all_camps ))

            for _shard_id in _plunder_list:
                yield redis.hset( TPL_TREASURE_SHARD_GOT % _shard_id, self.cid, dumps( (self.cid, self.user.level, self.user.base_att.nick_name) ) )
                #log.info('For Test. add treasure shard got. cid: {0}, _shard_id: {1}.'.format( self.cid, _shard_id ))

            #if treasure_id not in _treasure_ids:
            #    _treasure_ids.append( treasure_id )

        #if not _treasure_ids:
        #    yield redis.hdel( HASH_TREASURE_CHARACTER_CAMP, self.cid )

        #yield redis.hset( HASH_TREASURE_CHARACTER_IDS, self.cid, dumps(_treasure_ids) )
        #log.info('For Test. all treasure ids. cid: {0}, _treasure_ids: {1}.'.format( self.cid, _treasure_ids ))

    @defer.inlineCallbacks
    def create_table_data(self, item_type, item_id, item_num, time_now):
        yield self._load()
        gsattrib = GSAttribute( self.cid, GSBagTreasureShardMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, item_type=item_type, item_id=item_id, item_num=item_num, deleted=0, create_time=time_now, update_time=time_now, del_time=0, aux_data='' )
        if res_err:
            log.error('GSBagTreasureShardMgr create table data error. ')
            defer.returnValue( (UNKNOWN_ERROR, None) )

        self.__gsattribs[gsattrib.attrib_id] = gsattrib
        defer.returnValue( (NO_ERROR, gsattrib) )

    @defer.inlineCallbacks
    def dec_shard(self, shard_id):
        '''
        @summary: 通过碎片ID 减少玩家背包中的碎片。
            同时维护redis data-TPL_TREASURE_SHARD_GOT
        '''
        yield self._load()
        item_conf = get_item_by_itemid( shard_id )
        if not item_conf:
            log.error('Can not find conf. shard_id: {0}.'.format( shard_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )
        for sid, shard in self.__gsattribs.iteritems():
            if shard.item_id == shard_id:
                if shard.item_num > 1:
                    shard.item_num -= 1
                else:
                    shard.delete()
                    del self.__gsattribs[sid]
                break
        else:
            log.warn("user<{0}> have no the shard:{1}.".format(self.cid, shard_id))

        # 碎片可合成的宝物信息
        _, treasure_id, _ = item_conf['ChangeList'][0]
        yield self.update_avoid_cache( treasure_id )

    @defer.inlineCallbacks
    def delete_table_data(self, attrib_id):
        '''
        @summary: 通过玩家碎片ID 使用宝物碎片。单个碎片可无限叠加, 
            同时维护redis data-TPL_TREASURE_SHARD_GOT
        '''
        if self.__gsattribs.has_key( attrib_id ):
            gsattrib = self.__gsattribs[attrib_id]
            gsattrib.item_num -= 1
            if 1 > gsattrib.item_num:
                gsattrib.delete()
                del self.__gsattribs[attrib_id]

            item_conf = get_item_by_itemid( gsattrib.item_id )
            if item_conf:
                # 碎片可合成的宝物信息
                _, treasure_id, _ = item_conf['ChangeList'][0]
                yield self.update_avoid_cache( treasure_id )
            else:
                log.error('Can not find conf. cid: {0}, shard_id: {1}.'.format( self.cid, gsattrib.item_id ))
        else:
            log.error('Can not find user sahrd. cid: {0}, _uid: {1}.'.format( self.cid, attrib_id ))

    @defer.inlineCallbacks
    def combine(self, user_treasureshard_ids):
        '''
        @summary: 合成宝物碎片得到宝物
        '''
        yield self._load()
        used_item_ids = [] # 碎片道具ID列表
        shard_changelist = []
        # 检查材料的有效性
        for _uid in user_treasureshard_ids:
            if not self.__gsattribs.has_key( _uid ):
                log.error('Unknown user treasureshard. _uid: {0}.'.format( _uid ))
                defer.returnValue( UNKNOWN_TREASURESHARD )
            gsattrib  = self.__gsattribs[_uid]
            item_conf = get_item_by_itemid( gsattrib.item_id )
            if not item_conf:
                log.error('Can not find conf. item_id: {0}.'.format( item_id ))
                defer.returnValue( NOT_FOUND_CONF )
            if shard_changelist:
                if shard_changelist != item_conf['ChangeList']:
                    log.error('Treasureshard error. _uid: {0}, shard_changelist: {1}, item_conf: {2}.'.format( _uid, shard_changelist, item_conf ))
                    defer.returnValue( UNKNOWN_ITEM_ERROR )
            else:
                shard_changelist = item_conf['ChangeList']
            # 判断道具数量
            if 1 > gsattrib.item_num:
                log.error('error. _uid: {0}, cur item num: {1}.'.format( _uid, gsattrib.item_num ))
                defer.returnValue( CHAR_ITEM_NOT_ENOUGH )
            used_item_ids.append( gsattrib.item_id )
        # 获取要合成的宝物
        if 1 != len(shard_changelist):
            log.error('error. shard_changelist: {0}.'.format( shard_changelist ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )
        # format: [item_type, item_id, item_num]
        target_treasure = shard_changelist[0]
        target_conf = get_item_by_itemid( target_treasure[1] )
        if not target_conf:
            log.error('Can not find target conf. item_id: {0}.'.format( target_treasure[1] ))
            defer.returnValue( NOT_FOUND_CONF )
        # 检查合成宝物所需材料是否满足条件
        need_item_ids = [_c[1] for _c in target_conf['ChangeList']]
        if sorted(need_item_ids) != sorted(used_item_ids):
            log.error('shard can not combine. need_item_ids: {0}, used_item_ids: {1}.'.format( need_item_ids, used_item_ids ))
            defer.returnValue( REQUEST_LIMIT_ERROR )
        # 删除材料
        for _uid in user_treasureshard_ids:
            yield self.delete_table_data( _uid )
        # 新增宝物
        res_err, add_items = yield self.user.bag_treasure_mgr.new( target_treasure[1], target_treasure[2], WAY_AVOID_WAR )
        # 开服七天
        _conf = get_item_by_itemid(target_treasure[1])
        if not _conf:
            log.error('Can not find conf. item_id: {0}.'.format( item_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )
        if _conf['Quality'] >= 2:
            yield self.user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_9, 1)
            yield self.user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_9, 1)
        if not res_err and add_items:
            defer.returnValue( (add_items[0][0], add_items[0][2]) )

        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def gm_treasureshard_info(self):
        yield self._load()
        _treasureshard_info = []
        for attrib in self.__gsattribs.itervalues():
            _treasureshard_info.append( {'user_item_id':attrib.attrib_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'item_cnt':attrib.item_num, 'level':0, 'refine':[], 'exp':0, 'refine_level':0} )

        defer.returnValue( _treasureshard_info )



