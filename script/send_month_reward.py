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
game_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../gameserver')
sys.path.insert(0, lib_path)
sys.path.insert(0, game_path)

import py_txredisapi as REDIS

from twisted.internet import defer
from twisted.internet import reactor

from db_conf     import db_conf, redis_conf
from marshal     import loads, dumps
from time import time

redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

redis_key = 'HASH_MONTHLY_CARD'
'''
send monthly card reward
'''

@defer.inlineCallbacks
def send_monthly_card_reward():
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()

    cid_sql = 'select id, monthly_card from tb_character' 
    update_sql = 'update tb_character set monthly_card = %s where id = %s'

    print 'send begin!'
    
    cursor.execute( cid_sql )
    _all_cid = cursor.fetchall()
    for _cid, _month in _all_cid:
        if _month:
            _month -= 1
            if _month == 0:
                yield redis.hdel(redis_key, _cid)
            else:
                card_data = (time(), 0)
                yield redis.hset(redis_key, _cid, dumps(card_data))
            _primary = yield redis.hincrby( 'HASH_HINCRBY_KEY', 'AWARD_ID', 1 )
            _data    = [_primary, 4, [time()]]
            yield redis.hset( 'HASH_AWARD_CENTER_%s' % _cid, _primary, dumps(_data) )
            cursor.execute(update_sql % (_month, _cid))

    cursor.close()
    conn.close()
 
    print 'end...'
    conn   = None
    cursor = None
    reactor.stop()


if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, send_monthly_card_reward)
    reactor.run()




