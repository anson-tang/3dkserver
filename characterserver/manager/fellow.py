#!/usr/bin/env python
#-*-coding: utf-8-*-

from manager.base   import MetaAttrManager
from constant       import *
from table_fields   import TABLE_FIELDS

class CSFellowMgr(object):
    __metaclass__ = MetaAttrManager

    _table  = 'fellow'
    _fields = TABLE_FIELDS['fellow'][0]
    _time_fields = TABLE_FIELDS['fellow'][1]

    def __init__(self, user, cid):
        self.where = {'cid':cid, 'deleted':0}
        user.register(CSFellowMgr._table, self)

    def keys(self):
        return self.dict_attribs.keys()

    #def register(self, user):
    #    user.register(self._table, self)


