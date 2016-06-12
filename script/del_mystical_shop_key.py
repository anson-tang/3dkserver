#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import sys
sys.path.insert(0, '../lib')

import py_txredisapi as REDIS

from twisted.internet import defer
from twisted.internet import reactor
from db_conf          import redis_conf


redis = None

def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

'''
删除以下redis key:
    # 神秘商店
    HASH_MYSTICAL_SHOP
'''

@defer.inlineCallbacks
def get_data():
    del_key = 'HASH_MYSTICAL_SHOP'

    if del_key:
        yield redis.delete(del_key, '')
    print 'delete keys success.'

if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, get_data)
    reactor.run()




