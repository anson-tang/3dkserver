#!/usr/bin/env python
#-*-coding: utf-8-*-

from twisted.internet import defer
from protocol_manager import cs_call
from time import time

from log import log
from errorno import *
from constant import *

from manager.gsattribute import GSAttribute

from system import sysconfig

import bisect

#The gs_att is a GSAtrribute. Make sure it has these fields: item_type, item_id, user_item_id, count
#The cod in this page will be userd on : normal items ( no extra dynamic data), equip ( with extra dynamic data), etc.
class GSBagItem(object):
    def __init__(self, gs_att):
        self.gs_att = gs_att

    def __cmp__(self, other):
        self_sk    = self.item_id * 10000 + self.item_type
        other_sk = other.item_id * 10000 + other.item_type
        if self_sk < other_sk:
            return -1
        elif self_sk > other_sk:
            return 1
        else:
            return 0
            #if self.count < other.count:
            #    return -1
            #elif self.count > other.count:
            #    return 1
            #else:
            #    return 0

    def isSame(self, other):
        if self.item_type == other.item_type and self.item_id == other.item_id:
            return True
        else:
            return False

    @property
    def user_item_id(self):
        return self.gs_att.attrib_id

    @property
    def count(self):
        return self.gs_att['count']

    @property
    def item_type(self):
        return self.gs_att['item_type']

    @property
    def item_id(self):
        return self.gs_att['item_id']

    @property
    def count(self):
        return self.gs_att['count']

    def addItemCount(self, add):
        self.gs_att['count'] += add

    def setItemCount(self, count):
        self.gs_att['count'] = count

class GSBag(object):
    _tbl_name = ''
    _item_field_set = set()

    def __init__(self, cid, capacity):
        self.__cid = cid
        self.__capacity = capacity
        self.__list = []#List-ele: user_item_id. Value: GSBagItem

    def clear(self):
        self.__list = []

    def getCapacity(self):
        return self.__capacity

    def setCapacity(self, capacity):#Return: bool
        if capacity <  self.__capacity:
            self.__capacity = capacity
            return True
        else:
            return False

    def printAll(self):
        log.debug('Print all. type, id, count, uiid ///////////////////////////////////////////////////');
        for item in self.__list:
            log.debug('{0} - {1}, count {2}, uiid {3}'.format( item.item_type, item.item_id, item.count, item.user_item_id ))

    def loadItemDataFromCS(self, dic_item_data):
        #log.debug('[ GSBag::loadItem ] start. cid {0}, dic_item_data {1}, /////////////////////////////////////////'.format( self.__cid, dic_item_data ))
        for k, d in dic_item_data.iteritems():
            gs_att = GSAttribute(self.__cid, self._tbl_name, d['id'], self._item_field_set)
            gs_att.updateGSAttribute(False, d)
            new_item = GSBagItem(gs_att)

            bisect.insort_left(self.__list, new_item)
        log.debug('[ GSBag::loadItem ] end. cid {0}, count {1}'.format( self.__cid, len(self.__list) ))

    @defer.inlineCallbacks
    def createItemViaCS(self, item_type, item_id, add_count):#Return item inst if succeed, else return None
        try:
            res_create = yield cs_call('cs_create_item', (self.__cid, item_type, item_id, add_count))
        except Exception as e:
            log.exception()
            defer.returnValue(None)
            
        err, new_item_data = res_create
        gs_att = GSAttribute(self.__cid, self._tbl_name, new_item_data['id'], self._item_field_set)
        gs_att.updateGSAttribute(False, new_item_data)
        new_item = GSBagItem(gs_att)
        defer.returnValue(new_item)

    def findLeftmostSameOne(self, start_pos):#Return: Same one pos on leftmost
        start_item = self.__list[start_pos]
        leftmost = start_pos
        cur = start_pos - 1
        while cur >= 0:
            cur_item = self.__list[cur]
            if cur_item.isSame(start_item):
                leftmost = cur
            else:
                break
            cur -= 1
        return leftmost

    def dispatchAddCount(self, leftmost, add_count, max_pile):
        start_item = self.__list[leftmost]
        for cur in range(leftmost, len(self.__list)):
            cur_item = self.__list[cur]
            if cur_item.isSame(start_item):
                add_allowable = max_pile - cur_item.count
                if add_allowable > 0:
                    if add_allowable > add_count:
                        add_allowable = add_count
                    cur_item.addItemCount(add_allowable)
                    add_count -= add_allowable
                    log.debug('dispatchAddCount, item {0}-{1}, cur {2}, add {3}'.format( cur_item.item_type, cur_item.item_id, cur, add_allowable ))
            else:
                log.debug('dispatchAddCount, item {0}-{1}, break on pos {2}'.format( cur_item.item_type, cur_item.item_id, cur ))
                break
            if 0 == add_count:
                log.debug('dispatchAddCount, complete.')
                break
        return add_count

    @defer.inlineCallbacks
    def addItem(self, add_item_type, add_item_id, add_count, partial_add=False):#Return item inst if succeed, else return None.

        if add_count > BAG_MAX_PILE:
            log.warn('Exp3404361 Add count > max pile. Add count :', add_count)
            defer.returnValue(None)

        gs_att_find = GSAttribute(self.__cid, self._tbl_name, 0, self._item_field_set)
        gs_att_find.updateGSAttribute(False, { 'item_type':add_item_type , 'item_id':add_item_id, 'count':add_count })
        target_item = GSBagItem(gs_att_find)

        found_pos = bisect.bisect_left(self.__list, target_item)
        found_item = None
        log.debug('Find pos {0}'.format(found_pos))

        find_same = False
        if found_pos < 0 or found_pos >= len(self.__list):
            find_same = False
        else:
            found_item = self.__list[found_pos]
            if target_item.isSame( found_item ):
                find_same = True
            else:
                find_same = False

        if find_same:
            leftmost = self.findLeftmostSameOne(found_pos)
            found_item = self.__list[leftmost]
            log.debug('Leftmost pos {0}'.format(leftmost))
            add_count = self.dispatchAddCount(leftmost, add_count, BAG_MAX_PILE) #Try to dispath add count on existed (one or several ) items!

            count_sum = found_item.count + add_count
            if count_sum <= BAG_MAX_PILE:
                #Fully pile, just modify existing item's count.
                found_item.setItemCount(count_sum)
                defer.returnValue(found_item)
            else:
                if not partial_add:
                    #Add fail! Not allow partial pile!
                    pass
                else:
                    #Partial pile, ajust their count.
                    found_item.setItemCount(BAG_MAX_PILE)
                    add_count = count_sum - BAG_MAX_PILE

        if len(self.__list) >= self.__capacity:
            log.debug('[ GSBag::addItem ] Bag is full!  Cur capacity:', self.__capacity, ' partial_add:', partial_add)
            defer.returnValue(None)

        log.debug('[ GSBag::addItem ] Need create item via cs. cid {0}, type {1}, id {2}, count {3}'.format( self.__cid, add_item_type, add_item_id, add_count ))
        try:
            new_item = yield self.createItemViaCS(add_item_type, add_item_id, add_count)
        except Exception as e:
            log.exception();
            defer.returnValue(None)

        if not new_item:
            log.error('Exp39303873 create item via cs fail ! cid {0}, item {1}, {2}'.format( self.__cid, add_item_type, add_item_id ))
            defer.returnValue(None)

        bisect.insort_left(self.__list, new_item)

        defer.returnValue(new_item)

    def reduceItem(self, user_item_id, reduceCount):#Return True if succeed, else return False.
        idx = 0
        for item in self.__list:
            idx += 1
            if item.user_item_id == user_item_id:
                if item.count < reduceCount:
                    return False
                else:
                    new_count = item.count - reduceCount
                    item.setItemCount( new_count )

                    if item.count <= 0:
                        item['deleted'] = 1
                        item['del_time'] = int(time())
                        del self.__list[idx]
                    return True
        return False

    def getItemListForClient(self):
        res_list = []
        for item in self.__list:
            res_list.append( ( item.user_item_id, item.item_type, item.item_id, item.count ) )
        return res_list

    def getSpecifyItemCount(self, item_type, item_id):
        sum = 0
        for item in self.__list:
            if item.item_type == item_type and item.item_id == item_id:
                sum += item.count
        return sum

class GSBagNormal(GSBag):
    _tbl_name = 'bag_normal'
    _fields   = [ 'id', 'cid', 'item_type', 'item_id', 'count', 'deleted', 'create_time', 'update_time', 'del_time' ]
    _item_field_set = set( _fields )

