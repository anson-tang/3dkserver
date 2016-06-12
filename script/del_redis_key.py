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
#conf = {'dbid': 1, 'path': '/tmp/redis.sock'}

def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

'''
删除以下redis key:
    # 随机宝箱比重
    HASH_RANDOM_CHEST_%
    ## 夺宝概率 不动
    #HASH_TREASURESHARD_ROBOT_RATE_%s
    # 翻牌奖励 
    HASH_ACTIVITY_LOTTERY
    # 神秘商店
    HASH_MYSTICAL_SHOP
    HASH_MYSTICAL_LOTTERY
    # 副本掉落
    HASH_DUNGEON_DROP_RATE_%s

'''

@defer.inlineCallbacks
def get_data():
    del_keys = ['HASH_ACTIVITY_LOTTERY', 'HASH_MYSTICAL_SHOP', 'HASH_MYSTICAL_LOTTERY']
    # 随机宝箱比重
    all_keys = yield redis.keys('HASH_RANDOM_CHEST_*')
    print "total randon chest all_keys: ", len(all_keys)
    del_keys = all_keys

    ## 夺宝概率
    #all_keys = yield redis.keys('HASH_TREASURESHARD_ROBOT_RATE_*')
    #print "total treasureshard tobot rate all_keys: ", len(all_keys)
    #del_keys.extend( all_keys )

    # 副本掉落
    all_keys = yield redis.keys('HASH_DUNGEON_DROP_RATE_*')
    print "total dungeon drop all_keys: ", len(all_keys)
    del_keys.extend( all_keys )

    print "\ntotal del_keys: ", len(del_keys)
    if del_keys:
        yield redis.delete(del_keys, [])
    print 'delete keys success.'


if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, get_data)
    reactor.run()




