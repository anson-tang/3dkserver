#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2015 Don.Li
# Summary: 

from log      import log   
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     
from system   import sysconfig, get_package_oss_conf
from utils    import rand_num

from twisted.internet       import reactor
from twisted.internet.defer import inlineCallbacks, returnValue

PACKAGE_TYPE_NO_COUNT       = 0
PACKAGE_TYPE_PERSONAL_COUNT = 1
PACKAGE_TYPE_SERVER_COUNT   = 2

DICT_PACKAGE_SERVER_COUNTER = {}
@inlineCallbacks
def get_current_server_count(package_id):
    _cnt = 0
    
    if not DICT_PACKAGE_SERVER_COUNTER.has_key(package_id):
        _cnt = yield redis.hget(HASH_PACKAGE_SERVER_COUNTER, package_id)
        _cnt = int(_cnt) if _cnt else 0
        DICT_PACKAGE_SERVER_COUNTER[package_id] = _cnt
    else:
        _cnt = DICT_PACKAGE_SERVER_COUNTER[package_id]

    returnValue(_cnt)

DICT_PACKAGE_PERSONAL_COUNTER = {}
@inlineCallbacks
def get_current_personal_count(cid, package_id):
    if not DICT_PACKAGE_PERSONAL_COUNTER.has_key(package_id):
        _dict_cnt = yield redis.hgetall(HASH_PACKAGE_PERSONAL_COUNTER % package_id)
        DICT_PACKAGE_PERSONAL_COUNTER[package_id] = {int(k):int(v) for k, v in _dict_cnt.iteritems()}

    _dict_all_cnt = DICT_PACKAGE_PERSONAL_COUNTER[package_id]
    _cnt = _dict_all_cnt.get(cid, None)
    if _cnt is None:
        _cnt = 0
        _dict_all_cnt[cid] = _cnt

    returnValue(_cnt)

@inlineCallbacks
def inc_package_count(conf, cid, package_id):
    _personal_count_max, _server_count_max = conf

    if _server_count_max:
        _cnt = yield get_current_server_count(package_id)
        _cnt = _cnt + 1 if _cnt < _server_count_max else 0
        DICT_PACKAGE_SERVER_COUNTER[package_id] = _cnt

    if _personal_count_max:
        _cnt = yield get_current_personal_count(cid, package_id)
        _cnt = _cnt + 1 if _cnt < _personal_count_max else 0
        DICT_PACKAGE_PERSONAL_COUNTER[package_id][cid] = _cnt

@inlineCallbacks
def sync_redis():
    if DICT_PACKAGE_SERVER_COUNTER:
        yield redis.hmset(HASH_PACKAGE_SERVER_COUNTER, DICT_PACKAGE_SERVER_COUNTER)

    if DICT_PACKAGE_PERSONAL_COUNTER:
        for package_id, dict_personal_count in DICT_PACKAGE_PERSONAL_COUNTER.iteritems():
            yield redis.hmset(HASH_PACKAGE_PERSONAL_COUNTER % package_id, dict_personal_count)
reactor.addSystemEventTrigger('before', 'shutdown', sync_redis)

def get_package_count_conf(package_id):
    _conf = sysconfig['package_count'].get(package_id, None)
    if _conf:
        return _conf['PersonalCount'], _conf['ServerCount']

@inlineCallbacks
def package_open(user, package_id):
    _cid = user.cid
    package_id = int(package_id)

    _rand_from = PACKAGE_TYPE_NO_COUNT

    _conf = get_package_count_conf(package_id)
    if _conf:
        _personal_count_max, _server_count_max = _conf

        if _server_count_max:
            _cnt = yield get_current_server_count(package_id)
            if _cnt >= _server_count_max:
                _rand_from = PACKAGE_TYPE_SERVER_COUNT

        if _rand_from != PACKAGE_TYPE_SERVER_COUNT and _personal_count_max:
            _cnt = yield get_current_personal_count(_cid, package_id)
            if _cnt >= _personal_count_max:
                _rand_from = PACKAGE_TYPE_PERSONAL_COUNT

    _item_rand = rand_item_from_package(user, package_id, _rand_from)
    if _conf and _item_rand:
        inc_package_count(_conf, _cid, package_id)
    returnValue( _item_rand ) #format: item_type, item_id, item_num, need_notice

def rand_item_from_package(user, package_id, rand_from):
    _level     = user.level
    _vip_level = user.vip_level

    _all_conf  = sysconfig['package'].get(package_id, [])
    _all_conf  = _all_conf[rand_from] if _all_conf else []
    if not _all_conf:
        log.error('Not find basic conf. cid:{0}, package_id:{1}, rand_from:{2}.'.format( user.cid, package_id, rand_from ))

    _oss_conf = get_package_oss_conf(package_id, rand_from)
    _all_conf = _all_conf + _oss_conf
    if not _all_conf:
        log.error('Not find oss conf. cid:{0}, package_id:{1}, rand_from:{2}.'.format( user.cid, package_id, rand_from ))
        return None

    _rate_max  = 0
    _all_items = []
    for _conf in _all_conf:
        if _conf['RoleLevel'] <= _level and _conf['VipLevel'] <= _vip_level:
            _rate_max += _conf['Rate']
            _all_items.append((_conf['ItemType'], _conf['ItemID'], _conf['ItemNum'], _conf['Rate'], _conf['Notice']))

    _rand    = rand_num(_rate_max)
    _current = 0

    _item = None
    for _item_type, _item_id, _item_num, _rate, _notice in _all_items:
        _item = _item_type, _item_id, _item_num, _notice

        if _rand < (_current + _rate):
            break
        else:
            _current += _rate
    else:
        log.error('Rand empty. cid:{0}, level:{1}, vip:{2}, max:{3}, rand:{4}, current:{5}.'.format(
            user.cid, _level, _vip_level, _rate_max, _rand, _current))

    return _item
