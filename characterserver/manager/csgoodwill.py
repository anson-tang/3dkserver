#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 


from manager.base   import MetaAttrManager
from constant       import *
from table_fields   import TABLE_FIELDS

class CSGoodwillMgr(object):
    __metaclass__ = MetaAttrManager

    _table    = 'goodwill'
    _fields   = TABLE_FIELDS['goodwill'][0]
    _time_fields = TABLE_FIELDS['goodwill'][1]

    def __init__(self, user, cid):
        self.where = {'cid':cid}
        user.register(CSGoodwillMgr._table, self)



