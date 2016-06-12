#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Ethon Huang <huangxiaohen2738@gmail.com>
# License: Copyright(c) 2015 Ethon.Huang
# Summary: 


import MySQLdb
import sys
import os

reload(sys)
sys.setdefaultencoding('utf-8')


lib_path  = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
game_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../gameserver')
sys.path.insert(0, lib_path)
sys.path.insert(0, game_path)

import py_txredisapi as REDIS

from twisted.internet import defer
from twisted.internet import reactor

from db_conf     import db_conf, redis_conf
from marshal     import loads, dumps

from system      import get_all_achievement_conf

redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)

'''
update second achievement data
run it when server is running!
'''

SECOND_LIST = range(18, 25) + range(28, 34)

def get_standard_conf():
    _all_conf = get_all_achievement_conf()
    _d = {}
    if _all_conf:
        for acType, _info in _all_conf.iteritems():
            if acType in SECOND_LIST:
                for _id, _v in _info.iteritems():
                    status = 0
                    if _d.has_key(acType):
                        _d[acType][_id] = [status, 0]
                    else:
                        _d[acType] = {_id:[status,0]}
    return _d

@defer.inlineCallbacks
def sync_achievement():
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()

    cid_sql = 'select id, vip_level,friends from tb_character'
    fellow_sql = 'select count(*) from tb_fellow where cid = %s and on_troop != 0'
    goodwill_sql = 'select goodwill_level from tb_goodwill where cid = %s'
    fellow_level_sql = 'select max(level) from tb_fellow where cid = %s'
    treasure_refine_sql = 'select max(refine_level) from tb_bag_treasure where cid = %s'

    cursor.execute( cid_sql )
    _all_cid = cursor.fetchall()
    a = {}
    print 'select is running!'
    for _cid, _vip_level, friends in _all_cid:
        _d = get_standard_conf()
        for _type, _info in _d.iteritems():
            for _id, _v in _info.iteritems():
                if _type == 18:
                    #vip_level
                    _v[1] = _vip_level
                elif _type == 20:
                    #friends
                    total = len(loads(friends)) if friends else 0
                    _v[1] = total
                elif _type == 22:
                    #fellow num
                    cursor.execute(fellow_sql % _cid)
                    num = cursor.fetchone()
                    _v[1] = num[0]
                elif _type == 23:
                    #shenjiang
                    cursor.execute(goodwill_sql % _cid)
                    level = cursor.fetchall()
                    i = 0
                    for j in level:
                        i += j[0]
                    _v[1] = i
                elif _type == 28:
                    #fellow level
                    cursor.execute(fellow_level_sql % _cid)
                    num = cursor.fetchone()
                    if num[0] is not None:
                        num = int(num[0])
                    else:
                        num = 0
                    _v[1] = num
                elif _type == 33:
                    #treasure refine
                    cursor.execute(treasure_refine_sql % _cid)
                    num = cursor.fetchone()
                    _v[1] = num[0]
        a[_cid] = _d
    
    #alliance

    _st = yield redis.hgetall('HASH_ALLIANCE_INFO')
    for _, values in _st.iteritems():
        _info = loads(values)
        _, _, level, _, _, member, _ = _info
        for _id in member:
            for _type, _info in a[int(_id)].iteritems():
                if _type == 24:
                    for _, _v in _info.iteritems():
                        _v[1] = level

    _c = yield redis.hgetall('HASH_ALLIANCE_MEMBER')
    for _, _info in _c.iteritems():
        d = loads(_info)
        if d[8] == 0:
            for _type, _info in a[_id].iteritems():
                if _type == 24:
                    for _, _v in _info.iteritems():
                        _v[1] = 0

    print 'sync is beginning!'

    _stream = yield redis.hgetall("HASH_ACHIEVEMENT_INFO")
    for _cid, _info in _stream.iteritems():
        _data = loads(_info)
        _d = a[_cid]
        _datas = dict(_data.items() + _d.items())
        yield redis.hset("HASH_ACHIEVEMENT_INFO", _cid, dumps(_datas))

    cursor.close()
    conn.close()
 
    print 'end...'
    conn   = None
    cursor = None
    reactor.stop()


if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, sync_achievement)
    reactor.run()




