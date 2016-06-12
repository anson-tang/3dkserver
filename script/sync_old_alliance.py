#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import sys
sys.path.insert(0, '../lib')

import py_txredisapi as REDIS

from marshal          import loads, dumps
from twisted.internet import defer
from twisted.internet import reactor
from db_conf          import redis_conf


redis = None

def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

'''
更新公会的基本信息 新增字段公告
'''

@defer.inlineCallbacks
def get_data():
    all_alliance_streams = yield redis.hgetall( 'HASH_ALLIANCE_INFO' )
    print "total alliances: ", len(all_alliance_streams)
    for alliance_id, stream in all_alliance_streams.iteritems():
        _load_data = list(loads(stream))
        if len(_load_data) != 6:
            continue
        _load_data.append( '' )
        #print alliance_id, _load_data
        yield redis.hset('HASH_ALLIANCE_INFO', alliance_id, dumps(_load_data))

    print 'update redis success.'


if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, get_data)
    reactor.run()




