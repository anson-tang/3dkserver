#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from rpc      import route
from log      import log
from constant import *
from db       import db

from twisted.internet    import defer



@route()
@defer.inlineCallbacks
def cs_offline_friends(p, req):
    cid, offline_cids = req

    fields = ['id', 'lead_id', 'nick_name', 'level', 'might']
    _sql   = 'SELECT {0} FROM tb_character WHERE {1};'.format(','.join(fields), '1 AND' + ' OR '.join( [' id=%s'%_cid for _cid in offline_cids]))
    _dataset = yield db.query(_sql)
    #log.info('For Test. _sql: {0}, _dataset: {1}.'.format( _sql, _dataset ))

    defer.returnValue( _dataset if _dataset else [] )
 
@route()
@defer.inlineCallbacks
def cs_offline_rand_friends(p, req):
    cid, count, level, except_cids = req

    _info  = []
    _sql   = "SELECT id,lead_id,nick_name,level,might FROM tb_character WHERE 1 AND level >= %s AND level <= %s AND id not in ('%s');"
    _limit = "', '".join(map(str, except_cids))
    _dataset = yield db.query(_sql%(level-5, level+5, _limit))
    if len(_dataset)>= count:
        _info = random.sample(_dataset, count)
    else:
        _dataset = yield db.query(_sql%(level-10, level+10, _limit))
        if len(_dataset)>= count:
            _info = random.sample(_dataset, count)
        else:
            _dataset = yield db.query(_sql%(0, 1000, _limit))
            if len(_dataset)>= count:
                _info = random.sample(_dataset, count)
            else:
                _info = _dataset

    defer.returnValue( _info )
 
@route()
@defer.inlineCallbacks
def cs_search_nick_name(p, req):
    cid, nick_name = req

    _info = []
    _sql  = "select id,lead_id,nick_name,level,might FROM tb_character WHERE nick_name like '%s'"
    _query = _sql%('%'+nick_name+'%')

    _dataset = yield db.query( _query )
    if _dataset:
        defer.returnValue( _dataset[:FRIEND_RAND_MAX_COUNT] )
    else:
        defer.returnValue( [] )


