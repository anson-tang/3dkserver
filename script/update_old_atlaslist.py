#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
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
更新图鉴的领奖记录 更新字段品级为品质
'''

@defer.inlineCallbacks
def get_data():
    all_streams = yield redis.hgetall( 'HASH_ATLASLIST_AWARD' )
    print "total record: ", len(all_streams)
    i = 0
    for cid, stream in all_streams.iteritems():
        _load_data = list(loads(stream))
        if not _load_data:
            continue
        i += 1
        _new_data = []
        for _d in _load_data:
            _new_data.append( (_d[0], _d[1], _d[2]-2) )
        if i < 2:
            print 'old_data: ', _load_data, 'new_data: ', _new_data
        yield redis.hset('HASH_ATLASLIST_AWARD', cid, dumps(_new_data))

    print 'update redis success.'
    reactor.stop()



if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, get_data)
    reactor.run()

