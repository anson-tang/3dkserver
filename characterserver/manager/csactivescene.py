#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from manager.base   import MetaAttrManager
from constant       import *
from table_fields   import TABLE_FIELDS

class CSActiveSceneMgr(object):
    __metaclass__ = MetaAttrManager

    _multirow = False
    _table    = 'activescene'
    _fields   = TABLE_FIELDS['activescene'][0]
    _time_fields = TABLE_FIELDS['activescene'][1]

    def __init__(self, user, cid):
        self.where = {'cid':cid}
        user.register(CSActiveSceneMgr._table, self)



