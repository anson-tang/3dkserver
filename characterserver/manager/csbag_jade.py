#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

from manager.base   import MetaAttrManager
from constant       import *
from log            import log
from table_fields   import TABLE_FIELDS

class CSBagJadeMgr(object):
    __metaclass__ = MetaAttrManager

    _table  = 'bag_jade'
    _fields = TABLE_FIELDS['bag_jade'][0]
    _time_fields = TABLE_FIELDS['bag_jade'][1]

    def __init__(self, user, cid):    
        log.debug('CSBagJadeMgr init.')
        self.where = {'cid':cid, 'deleted':0}
        user.register(CSBagJadeMgr._table, self)

