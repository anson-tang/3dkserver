#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


import sys
import os

curr_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
sys.path.insert(0, curr_path)

import py_txredisapi as REDIS

from marshal          import loads, dumps
from twisted.internet import defer
from twisted.internet import reactor
from db_conf          import redis_conf



'''
更新老月卡的数据
'''


redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

@defer.inlineCallbacks
def update_data():
    had_data = yield redis.exists('HASH_MONTHLY_CARD')
    if had_data:
        print 'script had done.'
        reactor.stop()
        defer.returnValue( 0 )

    all_streams = yield redis.hgetall('HASH_MONTHLY_CARD_REWARD')
    for cid, last_time in all_streams.iteritems():
        try:
            last_time = int(last_time)
            new_data  = dumps([last_time, 0])
            yield redis.hset('HASH_MONTHLY_CARD', cid, new_data)
        except Exception, e:
            print 'cid:', cid, 'error:', e

    print 'end...'
    reactor.stop()

if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, update_data)
    reactor.run()





