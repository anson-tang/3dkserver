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
from system      import get_all_achievement_conf, get_item_by_itemid

redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)


def get_standard_conf():
    _all_conf = get_all_achievement_conf()
    _d = {}
    if _all_conf:
        for acType, _info in _all_conf.iteritems():
            for _id, _v in _info.iteritems():
                status = 0
                if _d.has_key(acType):
                    _d[acType][_id] = [status, 0]
                else:
                    _d[acType] = {_id:[status,0]}
    return _d
'''
update achievement data
run it when server is running!
'''

@defer.inlineCallbacks
def sync_achievement():
    i = 1
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()

    cid_sql = 'select id, level,vip_level,friends,might from tb_character where level > 1;'
    scene_sql = 'select max(dungeon_id), count(dungeon_star) from tb_scene where cid = %s;' 
    climb_sql = 'select max_layer from tb_climbing_tower where cid = %s;'
    jade_sql = 'select item_id from tb_bag_jade where del_time = 0 and cid = %s';
    
    cursor.execute( cid_sql )
    _all_cid = cursor.fetchall()
    a = {}
    print 'select is running!'
    for _cid, _lv, _vip_level, friends, might in _all_cid:
        cursor.execute(scene_sql % _cid)
        _max_id = cursor.fetchone()
        #lv
        if a.has_key(_cid):
            a[_cid].append([4, _lv])
        else:
            a[_cid] = [[4, _lv]]
        #vip_level
#       a[_cid].append([18, _vip_level])
        #scene
        if _max_id[0] is not None:
            a[_cid].append([3, _max_id[0]])
        #chaos
        a[_cid].append([11, _max_id[1]])
        #friends
#       total = len(loads(friends)) if friends else 0
#       a[_cid].append([20, total])
        #might
        a[_cid].append([14, might])
        #arena
        _rank = yield redis.zscore( "SET_ARENA_CID_RANK", _cid )
        _rank = int(_rank) if _rank else 0
        a[_cid].append([7, _rank])
        #elite
        _s = yield redis.hget("HASH_ELITESCENE_PASSED", _cid)
        if _s:
            passed_elitescene_ids = loads(_s)
            passed_elitescene_ids.sort()
            a[_cid].append([12, passed_elitescene_ids[-1]])
        #climb
        cursor.execute(climb_sql % _cid)
        _c = cursor.fetchone()
        if _c is not None:
            a[_cid].append([10, _c[0]])
        #jade
        cursor.execute(jade_sql % _cid)
        row = cursor.fetchall()
        i = 0
        for r in row:
            if get_item_by_itemid(int(r[0])).get('Quality', 0) >= 2:
                i += 1
        a[_cid].append([16, i]) 


    print 'sync is beginning!'

    for _cid, _info in a.iteritems():
        _d = get_standard_conf()
        for _type, _value in _info:
            for _, _v in _d[_type].iteritems():
                _v[1] = _value
        yield redis.hset("HASH_ACHIEVEMENT_INFO", _cid, dumps(_d))

    print 'sync scene end'


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




