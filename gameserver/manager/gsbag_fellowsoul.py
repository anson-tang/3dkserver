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

from syslogger              import syslogger
from twisted.internet       import defer
from system                 import get_item_by_itemid
from manager.gsattribute    import GSAttribute


class GSBagFellowsoulMgr(object):
    '''
    @summary: 玩家分魂背包
    '''
    _table     = 'bag_fellowsoul'

    def __init__(self, user):
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
                self.__gsattribs = yield GSAttribute.load( self.cid, GSBagFellowsoulMgr._table )

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
    def get(self, user_item_id):
        yield self._load()
        defer.returnValue( self.__gsattribs.get(user_item_id, None) )

    @defer.inlineCallbacks
    def get_fellowsouls(self, item_id, user_item_id=0):
        yield self._load()

        total_num, item_attribs = 0, []
        # 获取item id的最大叠加数
        item_conf = get_item_by_itemid( item_id )
        if not item_conf:
            log.error('Can not find conf. item_id: {0}.'.format( item_id ))
            defer.returnValue( (total_num, item_attribs) )
        MAX_NUM = item_conf['MaxOverlyingCount']

        for attrib in self.__gsattribs.itervalues():
            if attrib.item_id == item_id and attrib.item_num > 0:
                total_num += attrib.item_num
                if attrib.item_num < MAX_NUM:
                    item_attribs.insert(0, attrib)
                else:
                    item_attribs.append( attrib )

        defer.returnValue( (total_num, item_attribs) )

    @defer.inlineCallbacks
    def use(self, item_id, item_num):
        '''
        @summary: 先使用数量少的, 接着使用已满叠加数的分魂
        '''
        # used item attrib
        used_attribs = []
        total_num, item_attribs = yield self.get_fellowsouls( item_id )
        if item_num > total_num:
            log.error('Item id: {0}, need num: {1}, cur num: {2}.'.format( item_id, item_num, total_num ))
            defer.returnValue( [CHAR_ITEM_NOT_ENOUGH, used_attribs] )

        for attrib in item_attribs:
            if attrib.item_num < item_num:
                item_num -= attrib.item_num
                attrib.item_num = 0
            else:
                attrib.item_num -= item_num
                item_num = 0
            # save used item attrib
            used_attribs.append( attrib )

            if attrib.item_num == 0:
                self.delete_table_data( attrib.attrib_id )

            if 0 == item_num:
                break

        defer.returnValue( (NO_ERROR, used_attribs) )

    @property
    @defer.inlineCallbacks
    def value_list(self):
        yield self._load()
        value_list = []
        for attrib in self.__gsattribs.itervalues():
            value_list.append( (attrib.attrib_id, attrib.item_id, attrib.item_num) )

        defer.returnValue( (len(value_list), value_list) )

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
        if item_type not in BAG_FELLOWSOUL:
            log.error('new. Item type error. item_id: {0}.'.format( item_id ))
            defer.returnValue( (ITEM_TYPE_ERROR, None) )

        time_now   = int(time()) #datetime2string()
        MAX_NUM    = item_conf['MaxOverlyingCount'] or (2 ** 16 - 1)
        new_items  = []
        for attrib in self.__gsattribs.itervalues():
            if item_type == attrib.item_type and item_id == attrib.item_id and MAX_NUM > attrib.item_num:
                if (attrib.item_num + item_num) <= MAX_NUM:
                    attrib.item_num += item_num
                    new_items = self.add_new_items( [attrib.attrib_id, item_type, item_id, item_num], new_items )
                else:
                    add_num         = MAX_NUM - attrib.item_num
                    item_num        = item_num - add_num
                    attrib.item_num = MAX_NUM
                    new_items = self.add_new_items( [attrib.attrib_id, item_type, item_id, add_num], new_items )
                    continue
                break
        else:
            cur_item_num = item_num
            while cur_item_num >= MAX_NUM:
                errorno, new_attrib = yield self.create_table_data(item_type, item_id, MAX_NUM, time_now)
                if errorno:
                    defer.returnValue( (UNKNOWN_ERROR, None) )
                cur_item_num -= MAX_NUM
                new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, MAX_NUM], new_items )
            else:
                if cur_item_num > 0:
                    errorno, new_attrib = yield self.create_table_data(item_type, item_id, cur_item_num, time_now)
                    if errorno:
                        defer.returnValue( (UNKNOWN_ERROR, None) )
                    new_items = self.add_new_items( [new_attrib.attrib_id, item_type, item_id, cur_item_num], new_items )

        # add syslog
        for _item in new_items:
            syslogger(LOG_FELLOW_GET, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _item[0], _item[2], item_conf['QualityLevel'], item_conf['StarLevel'], way_type, way_others)
        defer.returnValue( (NO_ERROR, new_items) )

    @defer.inlineCallbacks
    def create_table_data(self, item_type, item_id, item_num, time_now):
        gsattrib = GSAttribute( self.cid, GSBagFellowsoulMgr._table )
        res_err  = yield gsattrib.new( cid=self.cid, item_type=item_type, item_id=item_id, item_num=item_num, deleted=0, create_time=time_now, update_time=time_now, del_time=0, aux_data='' )
        if res_err:
            log.error('GSBagFellowsoulMgr create table data error. ')
            defer.returnValue( (UNKNOWN_ERROR, None) )

        self.__gsattribs[gsattrib.attrib_id] = gsattrib
        defer.returnValue( (NO_ERROR, gsattrib) )

    def delete_table_data(self, attrib_id):
        if self.__gsattribs.has_key( attrib_id ):
            gsattrib = self.__gsattribs[attrib_id]
            gsattrib.delete()
            del self.__gsattribs[attrib_id]
        else:
            log.error('Can not find delete data. uid: {0}.'.format( attrib_id ))

    @defer.inlineCallbacks
    def combine(self, attrib_id):
        ''' 
        @summary: 碎片合成 
        @param  : attrib_id-玩家分魂ID
        '''
        attrib = yield self.get( attrib_id )
        if not attrib:
            log.error('combine. Can not find attrib_id. attrib_id: {0}.'.format( attrib_id ))
            defer.returnValue( (UNKNOWN_ERROR, None) )

        item_conf = get_item_by_itemid( attrib.item_id )
        if not item_conf:
            log.error('Can not find conf. item_id: {0}.'.format( attrib.item_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )

        # check limit
        # ChangeList format: [[target_item_type, target_item_id, need_item_num]]
        change_list = item_conf['ChangeList'] 
        if not change_list or len(change_list) > 1 or len(change_list[0]) < 3:
            log.error('Can not find item change_list conf. item_id: {0}.'.format( attrib.item_id ))
            defer.returnValue( (NOT_FOUND_CONF, None) )

        if attrib.item_num < change_list[0][2]:
            log.error("User's item not enough. have item: {0}, need item: {1}.".format( attrib.item_num, change_list[0][2] ))
            defer.returnValue( (CHAR_ITEM_NOT_ENOUGH, None) )

        _c = get_item_by_itemid(change_list[0][1]) 
        _quality = _c.get('Quality', 0)
        if _quality >= 2:
            yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_28, 1)
        if _quality >= 3:
            yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_29, 1)
        if _quality >= 4:
            yield self.user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_30, 1)
        # create new item
        # del current attrib
        self.delete_table_data( attrib_id )
        defer.returnValue( (NO_ERROR, change_list[0][1]) )

    @defer.inlineCallbacks
    def gm_fellowsoul_info(self):
        yield self._load()
        _fellowsoul_info = []
        for attrib in self.__gsattribs.itervalues():
            _fellowsoul_info.append( {'user_item_id':attrib.attrib_id, 'item_type':attrib.item_type, 'item_id':attrib.item_id, 'item_cnt':attrib.item_num, 'level':0, 'refine':[], 'exp':0, 'refine_level':0} )

        defer.returnValue( _fellowsoul_info )


