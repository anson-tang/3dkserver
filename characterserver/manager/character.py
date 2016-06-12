#!/usr/bin/env python
#-*-coding: utf-8-*-

from manager.base   import MetaAttrManager
from constant       import *
from table_fields   import TABLE_FIELDS

class Character(object):
    __metaclass__ = MetaAttrManager

    _multirow = False
    _table    = 'character'
    _fields   = TABLE_FIELDS['character'][0]
    _time_fields = TABLE_FIELDS['character'][1]

    def __init__(self, cid=None):
        if cid:
            self.where = {'id':cid}

    @property
    def cid(self):
        if self.dict_attribs:
            return self.dict_attribs._Attribute__uid
        else:
            return 0

    def register(self):
        from manager.csuser import g_UserMgr
        if self.dict_attribs:
            user = g_UserMgr.register(self.dict_attribs._Attribute__uid, self._table, self)
            return user
        else:
            return None



