#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


import MySQLdb
import sys
sys.path.insert(0, '../lib')
sys.path.insert(0, '../gameserver')

import py_txredisapi as REDIS

from twisted.internet import defer
from twisted.internet import reactor

from system      import *
from db_conf     import db_conf, redis_conf
from marshal     import loads, dumps


redis = None
def connect():
    global redis
    redis = REDIS.lazyUnixConnectionPool(**redis_conf)


@defer.inlineCallbacks
def sync_elitescene():
    all_elitescene_conf = sysconfig['elitescene']
    if not all_elitescene_conf:
        defer.returnValue( 0 )

    yield redis.delete(['HASH_ELITESCENE_PASSED'], [])

    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    sql_select   = 'SELECT `id`, `level` FROM tb_character'
    sql_scene    = 'SELECT `cid`, `scene_id`, `dungeon_id`, `dungeon_star` FROM tb_scene WHERE `cid`=%s;'
 
 
    cursor.execute( sql_select )
    _dataset = cursor.fetchall()
 
    _params  = []
    for _cid, _level in _dataset:
        cursor.execute( sql_scene%_cid )
        _scenes = cursor.fetchall()

        all_scene_passed = {}
        for _cid, _scene_id, _dungeon_id, _dungeon_star in _scenes:
            _passed = all_scene_passed.get(_scene_id, all_scene_passed.setdefault(_scene_id, 1))
            if not _passed: # _passed: 0-未通过, 1-已通过
                continue
            if _dungeon_star <= 0:
                all_scene_passed[_scene_id] = 0
        # 更新玩家的前置副本数据
        passed_elitescene_ids = []
        for _conf in all_elitescene_conf.itervalues():
            _passed = all_scene_passed.get(_conf['SceneID'], 0)
            if not _passed:
                continue
            if _level < _conf['NeedRoleLevel']:
                continue
            passed_elitescene_ids.append( _conf['EliteSceneID'] )

        if passed_elitescene_ids:
            yield redis.hset('HASH_ELITESCENE_PASSED', _cid, dumps(passed_elitescene_ids))
            print '_cid', _cid, passed_elitescene_ids

    cursor.close()
    conn.close()
 
    print 'end...'
    conn   = None
    cursor = None


if __name__ == "__main__":
    reactor.callWhenRunning( connect )
    reactor.callLater(1, sync_elitescene)
    reactor.run()




