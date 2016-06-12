#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2014 Don.Li
# Summary: 

from twisted.internet.defer import inlineCallbacks, returnValue

from log            import log
from redis          import redis
from constant       import *

from manager.member import Member

def singleton( cls, *args, **kwargs ):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[ cls ] = cls( *args, **kwargs )
        return instances[ cls ]

    return _singleton

@singleton
class UserManager( object ):
    __dict = {}

    @inlineCallbacks
    def update( self, member, name, level, vip_level, might, rank, lead_id ):
        if not isinstance( member, Member):
            log.warn( 'member is not a Member instance. info:{0}'.format( member ) )
        else:
            if member.cid not in self.__dict:
                self.__dict[ member.cid ] = member

            yield member.login( name, level, vip_level, might, rank, lead_id )

    @inlineCallbacks
    def login(self, cid, name, level, vip_level, lead_id, might, rank ):
        _m = None

        if cid in self.__dict:
            _m = self.__dict[cid]
        else:
            _stream = yield redis.hget( HASH_ALLIANCE_MEMBER, cid )

            if _stream:
                _m = Member.load( _stream )
                if _m:
                    yield _m.clean_alliance()
                else:
                    log.warn('Unknown error')
                    returnValue( None )
            else:
                _m = Member( cid, name, lead_id, level, vip_level, might, rank, 0, 0, 0, 0 )

        yield self.update( _m, name, level, vip_level, might, rank, lead_id )

        returnValue( _m )

    def getUser( self, cid ):
        return self.__dict.get( cid, None )

    @inlineCallbacks
    def get_offline_user(self, cid):
        _m = self.__dict.get( cid, None )
        if not _m:
            # 离线的玩家
            _stream = yield redis.hget( HASH_ALLIANCE_MEMBER, cid )
            if _stream:
                _m = Member.load( _stream )

        returnValue( _m )

    @inlineCallbacks
    def get_alliance_members(self, member_cids):
        data = []
        for cid in member_cids:
            if cid in self.__dict:
                _m = self.__dict[cid]
                data.append( _m.info )
            else:
                _stream = yield redis.hget( HASH_ALLIANCE_MEMBER, cid )

                if _stream:
                    _m = Member.load( _stream )
                    if _m:
                        data.append( _m.info )
        returnValue( data )

    def addUser(self, member):
        if not isinstance( member, Member):
            log.warn( 'member is not a Member instance. info:{0}'.format( member ) )
            return

        if member.cid not in self.__dict:
            self.__dict[ member.cid ] = member

    @inlineCallbacks
    def logout( self, cid ):
        _m = self.getUser( cid )
        if _m:
            yield _m.logoff()

        returnValue( 0 )

g_UserMgr = UserManager()

