#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 


from marshal  import loads, dumps
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from system   import get_atlaslist_category_conf


from twisted.internet       import defer
from manager.gsattribute    import GSAttribute
from models.characterserver import gs_load_table_data, gs_create_table_data
from table_fields           import TABLE_FIELDS
from models.item            import *


class GSAtlaslistMgr(object):
    _table = 'atlaslist'
    _fields = TABLE_FIELDS['atlaslist'][0]

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

        self.atlaslist = GSAttribute(user.cid, GSAtlaslistMgr._table, user.cid)

        self.load_flag = False

        self.fellow_ids   = None
        self.equip_ids    = None
        self.treasure_ids = None

    @defer.inlineCallbacks
    def load(self):
        if self.load_flag:
            defer.returnValue( None )

        try:
            table_data = yield gs_load_table_data(self.cid, GSAtlaslistMgr._table)
            # 注意在收到返回消息后才能赋值
            self.load_flag = True
            if table_data:
                table_data = dict(zip(GSAtlaslistMgr._fields, table_data))
                self.atlaslist.updateGSAttribute( False, **table_data )
                self.fellow_ids   = loads(self.atlaslist.fellow_ids)
                self.equip_ids    = loads(self.atlaslist.equip_ids)
                self.treasure_ids = loads(self.atlaslist.treasure_ids)
            else:
                yield self.new()
        except Exception as e:
            log.error( 'Exception raise. e: {0}.'.format( e ))

    @defer.inlineCallbacks
    def new(self):
        self.fellow_ids, self.equip_ids, self.treasure_ids = [], [], []
        # 检查伙伴列表、宝物背包列表、装备背包列表

        init_data = [self.cid, dumps(self.fellow_ids), dumps(self.equip_ids), dumps(self.treasure_ids)]
        kwargs = dict(zip(GSAtlaslistMgr._fields[1:], init_data))
        create_data = yield gs_create_table_data(self.cid, GSAtlaslistMgr._table, **kwargs)
        if create_data:
            create_data = dict(zip(GSAtlaslistMgr._fields, create_data))
            self.atlaslist.updateGSAttribute( False, **create_data )
        else: # 新增数据失败
            self.load_flag = False
 
    @defer.inlineCallbacks
    def atlaslist_info(self, category_id, second_type):
        yield self.load()
        _category_conf = get_atlaslist_category_conf( category_id )
        _second_conf   = _category_conf.get(second_type, {})
        if not _second_conf:
            defer.returnValue( NOT_FOUND_CONF )

        if category_id == CATEGORY_TYPE_FELLOW:
            _had_get_ids = self.fellow_ids
        elif category_id == CATEGORY_TYPE_EQUIP:
            _had_get_ids = self.equip_ids
        elif category_id == CATEGORY_TYPE_TREASURE:
            _had_get_ids = self.treasure_ids
        else:
            defer.returnValue( CLIENT_DATA_ERROR )

        _second_count = 0
        _quality_data = []
        for _quality, _quality_conf in _second_conf.iteritems():
            _item_ids = []
            _quality_count = 0
            for _item in _quality_conf['Items']:
                if _item['ItemID'] in _had_get_ids:
                    _quality_count += 1
                    _item_ids.append( _item['ItemID'] )
            _second_count += _quality_count
            # 星级收齐的奖励
            if _quality_count >= len(_quality_conf['Items']):
                _award_status = 1
                _award_data = yield redis.hget(HASH_ATLASLIST_AWARD, self.cid)
                if _award_data:
                    _award_data = loads(_award_data)
                    if (category_id, second_type, _quality) in _award_data:
                        _award_status = 2
            else:
                _award_status = 0
            _quality_data.append( (_quality, _item_ids, _quality_count, _award_status) )

        _f_count, _e_count, _t_count = len(self.fellow_ids), len(self.equip_ids), len(self.treasure_ids)

        defer.returnValue( (_f_count, _e_count, _t_count, category_id, second_type, _second_count, _quality_data) )

    @defer.inlineCallbacks
    def new_atlaslist(self, category_id, second_type, quality, item_id):
        yield self.load()
        _category_conf = get_atlaslist_category_conf(category_id)
        _second_conf   = _category_conf.get(second_type, {})
        _quality_conf  = _second_conf.get(quality, {})
        if not _quality_conf:
            defer.returnValue( None )

        for _item in _quality_conf['Items']:
            if _item['ItemID'] == item_id:
                break
        else:
            defer.returnValue( None )

        if category_id == CATEGORY_TYPE_FELLOW:
            if item_id not in self.fellow_ids:
                self.fellow_ids.append( item_id )
                self.atlaslist.fellow_ids = dumps( self.fellow_ids )
        elif category_id == CATEGORY_TYPE_EQUIP:
            if item_id not in self.equip_ids:
                self.equip_ids.append( item_id )
                self.atlaslist.equip_ids = dumps( self.equip_ids )
        elif category_id == CATEGORY_TYPE_TREASURE:
            if item_id not in self.treasure_ids:
                self.treasure_ids.append( item_id )
                self.atlaslist.treasure_ids = dumps( self.treasure_ids )

        defer.returnValue( None )

    @defer.inlineCallbacks
    def atlaslist_award(self, category_id, second_type, quality):
        _award_data = yield redis.hget(HASH_ATLASLIST_AWARD, self.cid)
        if _award_data:
            _award_data = loads(_award_data)
        else:
            _award_data = []

        _new_award = (category_id, second_type, quality)
        if _new_award in _award_data:
            defer.returnValue( ATLASLIST_AWARD_HAD_ERROR )

        _category_conf = get_atlaslist_category_conf(category_id)
        _second_conf   = _category_conf.get(second_type, {})
        _quality_conf  = _second_conf.get(quality, {})
        if not _quality_conf or not _quality_conf['Awardlist']:
            defer.returnValue( NOT_FOUND_CONF )
 
        _award_data.append( _new_award )
        yield redis.hset(HASH_ATLASLIST_AWARD, self.cid, dumps( _award_data ))
        items_return = []
        for _type, _id, _num in _quality_conf['Awardlist']:
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown item type. cid: {0}, item_type: {1}, item_id: {2}, item_num: {3}.'.format( self.cid, _type, _id, _num ))
                continue
            res_err, value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_ATLASLIST_AWARD, CapacityFlag=False)
            if not res_err and value:
                for _v in value:
                    items_return = total_new_items( _v, items_return )

        defer.returnValue( items_return )



