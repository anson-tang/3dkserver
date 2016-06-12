#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


import MySQLdb
import sys
import os

lib_path  = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
sys.path.insert(0, lib_path)

import py_txredisapi as REDIS

from twisted.internet import defer
from twisted.internet import reactor

from db_conf     import db_conf, redis_conf
from marshal     import loads, dumps


redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)


@defer.inlineCallbacks
def sync_scene():

    yield redis.delete('SET_SCENE_CID_STAR', 'SET_CLIMBING_CID_LAYER')

    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    sql_select   = 'SELECT `id`, `level` FROM tb_character'
    sql_scene    = 'SELECT `cid`, sum(dungeon_star) FROM tb_scene WHERE `cid`=%s;'
    sql_climbing = 'SELECT `cid`, `max_layer` FROM tb_climbing_tower WHERE `cid`=%s;'
 

    cursor.execute( sql_select )
    _dataset = cursor.fetchall()
    
    i = 0.0
    total = len(_dataset)
    for _cid, _level in _dataset:
        i += 1
        # 副本总星数
        cursor.execute( sql_scene%_cid )
        _scenes = cursor.fetchall()
        for _, _had_star in _scenes:
            if not _had_star:
                _had_star = 0
            yield redis.zadd('SET_SCENE_CID_STAR', _cid, -_had_star)
            #print '_cid', _cid, _had_star, _scenes

        # 天外天层数
        cursor.execute( sql_climbing%_cid )
        _climbings = cursor.fetchall()
        for _, _max_layer in _climbings:
            if not _max_layer:
                _max_layer = 0
            yield redis.zadd('SET_CLIMBING_CID_LAYER', _cid, -_max_layer)
            #print '_cid', _cid, _max_layer, _climbings
        if i % 500 == 0 or i >= total:
            sys.stdout.write("\rProgress: %s %%. total:%s." % (round((i / total) * 100, 2), total))
            sys.stdout.flush()

    cursor.close()
    conn.close()
 
    print '\nend...'
    conn   = None
    cursor = None
    reactor.stop()


if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, sync_scene)
    reactor.run()




