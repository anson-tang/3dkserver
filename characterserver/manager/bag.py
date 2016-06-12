#!/usr/bin/env python
#-*-coding: utf-8-*-

from manager.base   import MetaAttrManager
from constant import *

class BagNormal(object):
    __metaclass__ = MetaAttrManager

    _table  = 'bag_normal'
    _fields = [ 'id', 'cid', 'item_type', 'item_id', 'count', 'deleted', 'create_time', 'update_time', 'del_time' ]

    def __init__(self, cid):    
        self.where = {'cid':cid, 'deleted':0}

    def keys(self):
        return self.dict_attribs.keys()

    def register(self, user):
        user.register(self._table, self)

