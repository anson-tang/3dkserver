#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from collections    import OrderedDict
from marshal        import loads, dumps
from datetime       import datetime
from log            import log
from errorno        import *
from constant       import *
from redis          import redis
from system         import get_item_by_itemid, get_goodwill_level_conf, get_goodwill_achieve_conf

from twisted.internet       import defer
from manager.gsattribute    import GSAttribute
from models.characterserver import gs_load_table_data, gs_create_table_data
from table_fields           import TABLE_FIELDS
from models.item            import *




class GSGoodwillMgr(object):
    _table = 'goodwill'

    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

        self.__goodwills = None
        self.total_goodwill_level = 0
        self.last_fellow_id = 0

        self.__loading = False
        self.__defers = []

    @defer.inlineCallbacks
    def _load(self):
        '''
        data format: {fellow_id: gsattrib, ...}
        '''
        if self.__goodwills is None:
            if not self.__loading:
                self.__loading = True
                gsattribs = yield GSAttribute.load(self.cid, GSGoodwillMgr._table)
                # 注意在收到返回消息后才能赋值
                self.__goodwills = OrderedDict()
                first_gsattrib   = None

                for gsattrib in gsattribs.itervalues():
                    if first_gsattrib is None:
                        first_gsattrib = gsattrib
                    if self.__goodwills.has_key( gsattrib.fellow_id ):
                        continue
                    self.__goodwills[gsattrib.fellow_id] = gsattrib

                    if gsattrib.last_gift:
                        if self.last_fellow_id > 0:
                            gsattrib.last_gift = 0
                        else:
                            self.last_fellow_id = gsattrib.fellow_id

                    self.total_goodwill_level += gsattrib.goodwill_level

                if first_gsattrib and not self.last_fellow_id:
                    self.last_fellow_id = first_gsattrib.fellow_id

                for d in self.__defers:
                    d.callback(True)

                self.__loading = False
                self.__defers  = []
            else:
                d = defer.Deferred()
                self.__defers.append(d)
                yield d

    @defer.inlineCallbacks
    def get_fellow(self, fellow_id):
        yield self._load()
        defer.returnValue( self.__goodwills.get(fellow_id, None) )

    @defer.inlineCallbacks
    def get_goodwill_list(self):
        yield self._load()
        _values = []
        for gsattrib in self.__goodwills.itervalues():
            _values.append( (gsattrib.fellow_id, gsattrib.goodwill_exp, gsattrib.goodwill_level) )

        defer.returnValue( (self.total_goodwill_level, self.last_fellow_id, _values) )

    @defer.inlineCallbacks
    def create_table_data(self, fellow_id):
        gsattrib = yield self.get_fellow(fellow_id)
        if gsattrib:
            defer.returnValue( (NO_ERROR, gsattrib) )

        gsattrib = GSAttribute(self.cid, GSGoodwillMgr._table)
        res_err  = yield gsattrib.new(cid=self.cid, fellow_id=fellow_id, goodwill_exp=0, goodwill_level=0, last_gift=0)
        if res_err:
            log.error('GSGoodwillMgr create table data error. ')
            defer.returnValue( (UNKNOWN_ERROR, None) )

        self.__goodwills[gsattrib.fellow_id] = gsattrib

        if self.last_fellow_id == 0:
            self.last_fellow_id = fellow_id

        defer.returnValue( (NO_ERROR, gsattrib) )

    @defer.inlineCallbacks
    def gift_goodwill(self, fellow_id, use_items):
        gsattrib = yield self.get_fellow(fellow_id)
        if not gsattrib:
            defer.returnValue( UNKNOWN_FELLOW_ERROR )

        level_conf = get_goodwill_level_conf(gsattrib.goodwill_level + 1)
        if not level_conf:
            defer.returnValue( GOODWILL_LEVEL_MAX_ERROR )
 
        get_goodwill, crit_count, levelup_count = 0, 0, 0
        items_return = []
        cur_goodwill_exp   = gsattrib.goodwill_exp
        cur_goodwill_level = gsattrib.goodwill_level
        del_items = {}

        all_item_ids = []
        for item_id, item_num in use_items:
            all_item_ids.extend( [item_id] * item_num )

        for item_id in all_item_ids:
            add_goodwill = 0
            item_conf = get_item_by_itemid( item_id )
            if not item_conf:
                continue
            for _attr in item_conf['attributes']:
                if _attr['AttributeID'] != ATTRIBUTE_TYPE_GOODWILL:
                    continue
                add_goodwill = _attr['Value']
            if add_goodwill == 0:
                continue
            del_items[item_id] = del_items.setdefault( item_id, 0 ) + 1
            # 计算好感度经验值
            get_goodwill += add_goodwill
            cur_goodwill_exp += add_goodwill
            if cur_goodwill_exp >= level_conf['PurpleExp']:
                cur_goodwill_exp, cur_goodwill_level, levelup_count = self.cal_level_up( cur_goodwill_exp, cur_goodwill_level, levelup_count )
                # 好感度升级conf
                level_conf = get_goodwill_level_conf(cur_goodwill_level + 1)
                if not level_conf:
                    break
            else:
                need_goodwill_exp = level_conf['PurpleExp'] - cur_goodwill_exp
                crit_ratio = level_conf['PurpleCrit'] + add_goodwill / need_goodwill_exp * 0.5
                rand_int = random.randint(1, 10000)
                if rand_int <= crit_ratio:
                    crit_count += 1
                    cur_goodwill_exp = 0
                    cur_goodwill_level += 1
                    levelup_count += 1
                    # 好感度升级conf
                    level_conf = get_goodwill_level_conf(cur_goodwill_level + 1)
                    if not level_conf:
                        break
        #log.info('For Test. del_items: {0}.'.format( del_items ))
        # 使用道具
        for _id, _num in del_items.items():
            res_err, used_attribs = yield self.user.bag_item_mgr.use( _id, _num )
            if res_err:
                continue
            for _a in used_attribs:
                items_return = total_new_items( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num], items_return )
  
        #log.info('For Test. cur_goodwill_exp: {0}, cur_goodwill_level: {1}, get_goodwill: {2}, crit_count: {3}, levelup_count: {4}.'.format( cur_goodwill_exp, cur_goodwill_level, get_goodwill, crit_count, levelup_count ))
        if cur_goodwill_exp != gsattrib.goodwill_exp:
            gsattrib.goodwill_exp = cur_goodwill_exp

        last_total_level = self.total_goodwill_level
        if cur_goodwill_level > gsattrib.goodwill_level:
            gsattrib.goodwill_level = cur_goodwill_level
            self.total_goodwill_level += levelup_count
            add_douzhan = yield self.check_achieve( last_total_level )
            if add_douzhan > 0:
                yield self.update_friend_gift_douzhan(add_douzhan)
        # 更新last_fellow_id
        gsattrib.last_gift = 1
        if self.last_fellow_id:
            last_gsattrib = yield self.get_fellow(self.last_fellow_id)
            if last_gsattrib:
                last_gsattrib.last_gift = 0

        self.last_fellow_id = fellow_id
 
        yield self.user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_13, 1)
        yield self.user.update_achievement_status(23, self.total_goodwill_level)
        defer.returnValue( (self.total_goodwill_level, cur_goodwill_exp, cur_goodwill_level, get_goodwill, crit_count, levelup_count, items_return) )

    def cal_level_up(self, total_exp, cur_level, levelup_count):
        level_conf = get_goodwill_level_conf(cur_level + 1)
        if not level_conf:
            return total_exp, cur_level, levelup_count

        while total_exp >= level_conf['PurpleExp']:
            cur_level += 1
            levelup_count += 1
            total_exp -= level_conf['PurpleExp']

            next_level_conf = get_goodwill_level_conf(cur_level + 1)
            if not next_level_conf:
                return level_conf['PurpleExp'], cur_level, levelup_count

            level_conf = next_level_conf

        return total_exp, cur_level, levelup_count

    @defer.inlineCallbacks
    def exchange_goodwill(self, left_fellow_id, right_fellow_id):
        if self.user.credits < EXCHANGE_GOODWILL_COST:
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )

        left_gsattrib  = yield self.get_fellow(left_fellow_id)
        right_gsattrib = yield self.get_fellow(right_fellow_id)
        if not left_gsattrib or not right_gsattrib:
            defer.returnValue( UNKNOWN_FELLOW_ERROR )
        # 扣钻石
        yield self.user.consume_credits(EXCHANGE_GOODWILL_COST, WAY_GOODWILL_EXCHANGE)
        # 互换好感等级和好感经验值
        left_goodwill_level = left_gsattrib.goodwill_level
        left_goodwill_exp   = left_gsattrib.goodwill_exp

        left_gsattrib.goodwill_level  = right_gsattrib.goodwill_level
        left_gsattrib.goodwill_exp    = right_gsattrib.goodwill_exp

        right_gsattrib.goodwill_level = left_goodwill_level
        right_gsattrib.goodwill_exp   = left_goodwill_exp

        defer.returnValue( [self.user.credits] )
    
    @defer.inlineCallbacks
    def check_achieve(self, last_total_level=0):
        ''' 返回[last_total_level, cur_total_level]区间可以新增的领取斗战点次数
        '''
        yield self._load()
        add_douzhan = 0
        if self.total_goodwill_level == 0:
            defer.returnValue( add_douzhan )

        achieve_conf = get_goodwill_achieve_conf()
        if not achieve_conf:
            defer.returnValue( add_douzhan )

        for _achieve in achieve_conf.itervalues():
            if _achieve['AttributeID'] != ATTRIBUTE_TYPE_DOUZHAN:
                continue
            if _achieve['AchieveValue'] < last_total_level:
                continue
            if _achieve['AchieveValue'] <= self.total_goodwill_level:
                add_douzhan += _achieve['AttributeValue']

        defer.returnValue( add_douzhan )

    @defer.inlineCallbacks
    def update_friend_gift_douzhan(self, add_douzhan):
        ''' 更新可领取斗战点最大次数 '''
        if add_douzhan <= 0:
            defer.returnValue( None )

        _data  = yield redis.hget( HASH_FRIENDS_GIFT_DOUZHAN % self.cid, FRIENDS_DOUZHAN_GET )
        if _data:
            last_time, left_count = loads( _data )
            dt_last = datetime.fromtimestamp( last_time )
            dt_now  = datetime.now()
            if dt_last.date() == dt_now.date():
                left_count += add_douzhan
                yield redis.hset( HASH_FRIENDS_GIFT_DOUZHAN % self.cid, FRIENDS_DOUZHAN_GET, dumps((last_time, left_count)) )



