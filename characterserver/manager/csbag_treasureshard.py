#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 


from manager.base   import MetaAttrManager
from constant       import *
from log            import log
from table_fields   import TABLE_FIELDS

class CSBagTreasureShardMgr(object):
    __metaclass__ = MetaAttrManager

    _table  = 'bag_treasureshard'
    _fields = TABLE_FIELDS['bag_treasureshard'][0]
    _time_fields = TABLE_FIELDS['bag_treasureshard'][1]

    def __init__(self, user, cid):    
        self.where = {'cid':cid, 'deleted':0}
        user.register(CSBagTreasureShardMgr._table, self)


