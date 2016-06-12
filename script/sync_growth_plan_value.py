#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb
import sys
sys.path.insert(0, '../lib')

import py_txredisapi as REDIS
from db_conf     import db_conf, redis_conf
from marshal import loads, dumps
from twisted.internet import defer
from twisted.internet import reactor
from time import time

redis = None

def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

@defer.inlineCallbacks
def get_data():
    '''
    更新成长计划redis数据结构
    '''
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    sql = 'select count(*) from tb_character where growth_plan > 0'
    num = cursor.execute( sql )
    conn.commit()
    _s = yield redis.hget("HASH_BUY_GROW_PLAN_TOTAL_NUM", "buy_grow_total_num")  
    if _s:
        total, times = loads(_s)
    else:
        total, times = int(num), time()
    yield redis.hset("HASH_BUY_GROW_PLAN_TOTAL_NUM", "buy_grow_total_num", dumps([total, times]))  
    print ' update end...'
    cursor.close()
    conn.close()
    conn   = None
    cursor = None


if __name__=="__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, get_data)
    reactor.run()


