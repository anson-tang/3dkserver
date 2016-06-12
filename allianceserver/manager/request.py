#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2014 Don.Li
# Summary: 

from twisted.internet.defer import inlineCallbacks, returnValue

from log      import log
from marshal  import loads, dumps
from time     import time
from redis    import redis
from constant import TPL_LIST_ALLIANCE_REQUEST


DICT_REQUEST = {}

def _add_request_to_dict( cid, request ):
    _added = False

    _reqs_in_dict = DICT_REQUEST.setdefault( cid, [] )
    for r in _reqs_in_dict:
        if r.alliance.aid == request.alliance.aid:
            return _added
    else:
        _reqs_in_dict.append( request )
        _added = True

    return _added

def del_request_to_dict( requests ):
    ''' 删除入会申请 
    '''
    for _r in requests:
        _reqs_in_dict = DICT_REQUEST.get(_r.cid, [])
        if _r in _reqs_in_dict:
            _reqs_in_dict.remove( _r )
            DICT_REQUEST[_r.cid] = _reqs_in_dict

def character_requests( cid ):
    return DICT_REQUEST.get( cid, [] )

class Request( object ):
    def __init__( self, cid, name, lead_id, level, might, rank, t = None, alliance = None, sync = False ):
        self.__cid         = cid
        self.__name        = name
        self.__lead_id     = lead_id
        self.__level       = level
        self.__might       = might
        self.__rank        = rank # 玩家的竞技场排名
        self.__t           = t if t else int( time() ) #申请时间

        self.alliance      = alliance

        if sync:
            self.sync()

    @property
    def cid( self ):
        return self.__cid

    @property
    def aid(self):
        return self.alliance.aid if self.alliance else -1

    @property
    def lead_id( self ):
        return self.__lead_id

    @property
    def name( self ):
        return self.__name

    @property
    def level( self ):
        return self.__level

    @property
    def might( self ):
        return self.__might

    @property
    def request_time(self):
        return self.__t

    @property
    def info(self):
        return [self.__cid, self.__name, self.__level, self.__lead_id, self.__might, self.__rank, self.__t]

    @staticmethod
    def load( stream, alliance ):
        try:
            _cid, _name, _level, _lead_id, _might, _rank, _t = loads( stream )
        except:
            log.exception()
            returnValue( None )

        _r = Request( _cid, _name, _lead_id, _level, _might, _rank, _t, alliance )
        _reqs_in_dict = DICT_REQUEST.setdefault(_cid, [])
        if _r not in _reqs_in_dict:
            DICT_REQUEST[_cid].append( _r )

        return _r

    @inlineCallbacks
    def sync( self ):
        #_info = self.__cid, self.__name, self.__lead_id, self.__level, self.__might, self.__rank, self.__t

        if self.alliance:
            yield redis.rpush( TPL_LIST_ALLIANCE_REQUEST % self.alliance.aid, dumps( self.info ) )
        else:
            log.warn( 'This Request<%s> have no alliance'.format( self.info ) )

    @staticmethod
    def new(cid, name, lead_id, level, might, rank, alliance):
        _t = int(time())
        _r = Request(cid, name, lead_id, level, might, rank, _t, alliance, True)
        _add_request_to_dict(cid, _r)
        return _r



