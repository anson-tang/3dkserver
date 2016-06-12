#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import config
import bisect

from time                       import time
from twisted.internet.protocol  import ServerFactory
from twisted.internet           import reactor, defer
from rpc                        import GeminiRPCProtocol, load_all_handlers
from os.path                    import abspath, dirname
from reconnect                  import ReConnectCreator
from protocol_manager           import protocol_manager
from manager.alliance           import Alliance
from manager.user               import g_UserMgr
from utils                      import get_reward_timestamp

from constant import HASH_ALLIANCE_INFO, PK_ALLIANCE_ID_AI, ALLIANCE_POSITION_LEADER
from errorno  import *
from redis    import redis

class Server(ServerFactory):
    protocol = GeminiRPCProtocol
    __alliances = []

    def startFactory(self):
        print '=============================\n'
        print '*   Alliance Server Start!   *\n'
        print '=============================', dirname(abspath(__file__)) + '/'
        load_all_handlers(dirname(abspath(__file__)) + '/', 'handler')

        self.load_all_alliance()

        self.connectGW()
        self.connectMS()

    def print_alliances(self):
        print 'total have alliance: ', len(Server.__alliances)
        for _a in Server.__alliances:
            print 'alliance_id: ', _a.aid, 'alliance_name: ', str(_a.name), 'alliance_info: ', a.info

    @property
    def alliances( self ):
        #print 'total have alliance: ', len(Server.__alliances)
        #for _a in Server.__alliances:
        #    print 'alliance_id: ', _a.aid, 'alliance_name: ', str(_a.name)
        return Server.__alliances

    def get_alliance(self, alliance_id):
        for _a in Server.__alliances:
            if _a.aid == alliance_id:
                return _a
        return None

    @defer.inlineCallbacks
    def load_all_alliance( self ):
        try:
            all_alliance_streams = yield redis.hgetall( HASH_ALLIANCE_INFO )

            for stream in all_alliance_streams.itervalues():
                _a = yield Alliance.load( stream )
                if not _a:
                    continue
                self.add_alliance( _a )

            _remain = get_reward_timestamp(23, 59, 59) - int(time())
            reactor.callLater(_remain, self.sync_alliance_rank)
        except Exception as e:
            reactor.callLater(1, self.load_all_alliance)
            print 'WARNING. Redis connection fail, callLater 1 second. e:', e

    def dirty_alliance(self, alliance):
        ''' 在有新成员加入的时候调用 '''
        _a = self.get_alliance( alliance.aid )
        if _a:
            Server.__alliances.remove(_a)

        self.add_alliance( alliance )

    def add_alliance(self, alliance):
        if alliance:
            bisect.insort_right( Server.__alliances, alliance )

    @defer.inlineCallbacks
    def sync_alliance_rank(self):
        _alliances = []
        for _a in Server.__alliances:
            _member_cids = _a.members
            _total_might = 0
            for _cid in _member_cids:
                _m = yield g_UserMgr.get_offline_user(_cid)
                if not _m:
                    continue
                _total_might += _m.might
            _a.set_might(_total_might)
            bisect.insort_right( _alliances, _a )

        Server.__alliances = _alliances
        _remain = get_reward_timestamp(23, 59, 59) - int(time())
        reactor.callLater(_remain, self.sync_alliance_rank)

    def rank(self, alliance):
        try:
            _total = len(Server.__alliances)
            _rank  = _total - Server.__alliances.index( alliance )
        except:
            _rank = 0

        return _rank

    @defer.inlineCallbacks
    def create_alliance( self, alliance_name, member ):
        _new_alli_id = yield redis.incr( PK_ALLIANCE_ID_AI )

        _alliance = Alliance( _new_alli_id, alliance_name, 1, 0, '', '' )

        #member.alliance = _alliance
        #member.update_position( ALLIANCE_POSITION_LEADER, False )
        member.join_alliance(_alliance, ALLIANCE_POSITION_LEADER)
        _alliance.add_member( member, dirty=True )
        # 注意调用时的顺序
        self.add_alliance( _alliance )

        defer.returnValue( _alliance )

    @defer.inlineCallbacks
    def dissolve_alliance(self, alliance_id):
        yield redis.hdel( HASH_ALLIANCE_INFO, alliance_id )
        _a = self.get_alliance( alliance_id )
        if not _a:
            defer.returnValue( ALLIANCE_UNKNOWN_ERROR )
        if len(_a.members) > 1:
            defer.returnValue( ALLIANCE_DISSOLVE_ERROR )
        # 更新公会的状态值
        _a.deleted = True
        # 清除公会的入会申请
        yield _a.del_all_requests()

        if _a in Server.__alliances:
            Server.__alliances.remove( _a )

        defer.returnValue( NO_ERROR )

    def filter_by_name( self, name ):
        return [ _a for _a in Server.__alliances if _a.name.find( name ) > -1]

    def cleanup(self):
        pass

    def stopFactory(self):
        print '=============================\n'
        print '*  Alliance Server Stop!     *\n'
        print '============================='

    def connectGW(self):
        ReConnectCreator(self.GWConnectionMade, config.gw_host, config.gw_port).connect()

    @defer.inlineCallbacks
    def GWConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'alli')
            
            print ('registedGW: result:%s, me:%s, peer:%s.' % (res, p.transport.getHost(), p.transport.getPeer()))
            if res[0] == 0:
                protocol_manager.set_server('gw', p)

    def connectMS(self):
        ReConnectCreator(self.MSConnectionMade, config.ms_host, config.ms_port).connect()

    @defer.inlineCallbacks
    def MSConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'gs')

            print ('registedMS: result: {0}, me: {1}, peer: {2}.'.format( res, p.transport.getHost(), p.transport.getPeer() ))
            if res[0] == 0:
                protocol_manager.set_server('ms', p)



try:
    server
except NameError:
    server = Server()


