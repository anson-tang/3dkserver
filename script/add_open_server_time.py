
# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import sys
import os

curr_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
sys.path.insert(0, curr_path)

import py_txredisapi as REDIS

from twisted.internet import defer
from twisted.internet import reactor
from db_conf          import redis_conf
from marshal          import dumps, loads

redis = None

def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)


@defer.inlineCallbacks
def get_data():
    print 'start!'
    data = [{}, 0, 0]
    yield redis.hset('HASH_OPEN_SERVER_INFO', "end_time", dumps(data))

    print 'add successful!'
    reactor.stop()

if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, get_data)
    reactor.run()




