#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Ethon Huang <huangxiaohen2738@gmail.com>
# License: Copyright(c) 2015 Ethon.Huang
# Summary: 


import MySQLdb
import sys
import os

lib_path  = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
sys.path.insert(0, lib_path)

from twisted.internet import defer
from twisted.internet import reactor

from db_conf     import db_conf, redis_conf
import py_txredisapi as REDIS
from marshal import loads

'''
send rename allinace card
'''

redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

@defer.inlineCallbacks
def send_rename_card():
    _leader_list = []
    print 'send begin!'
    _all = yield redis.hgetall('HASH_ALLIANCE_MEMBER')
    for cid, k in _all.iteritems():
        _position = loads(k)[8]
        if _position == 1:
            _leader_list.append(cid)
    print _leader_list
    #add_sql = ('insert into tb_bag_item (cid, item_type, item_id, item_num) values(%s, %s, %s, %s)')
    #conn = MySQLdb.connect(**db_conf)
    #cursor = conn.cursor()
    #res = []
    #for i in _leader_list:
    #   res.append((i, 8, 103, 1)) 
    #cursor.executemany(add_sql, res)
    #conn.commit()
    print 'end...'
    conn   = None
    cursor = None
    reactor.stop()
 

if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, send_rename_card)
    reactor.run()



