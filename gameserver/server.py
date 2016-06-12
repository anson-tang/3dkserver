#!/usr/bin/env python
#-*-coding: utf-8-*-

import config

from os.path                   import abspath, dirname
from twisted.internet.protocol import ServerFactory
from twisted.internet          import protocol, reactor, defer

from rpc                       import GeminiRPCProtocol, load_all_handlers
from reconnect                 import ReConnectCreator
from protocol_manager          import protocol_manager, gw_send

from log                       import log
from manager.gsuser            import g_UserMgr
from manager.gslimit_fellow    import check_limit_fellow
from manager.gsexcite_activity import check_excite_activity
from constant                  import EXCITE_PAY_ACTIVITY, EXCITE_CONSUME_ACTIVITY, EXCITE_GROUP_BUY
from models.worldboss          import worldBoss

class Server(ServerFactory):
    protocol = GeminiRPCProtocol

    def startFactory(self):
        print '=============================\n'
        print '*   Game Server Start!   *\n'
        print '============================='
        load_all_handlers(dirname(abspath(__file__)) + '/', 'handler')
        self.connectGW()
        self.connectCS()
        self.connectMS()
        self.connectAlliance()

        try:
            reactor.callLater(1, check_limit_fellow)
            reactor.callLater(1, check_excite_activity, EXCITE_PAY_ACTIVITY)
            reactor.callLater(1, check_excite_activity, EXCITE_CONSUME_ACTIVITY)
            reactor.callLater(1, check_excite_activity, EXCITE_GROUP_BUY)
            reactor.callLater(1, worldBoss.init)
        except Exception, e:
            reactor.callLater(1, check_limit_fellow)
            reactor.callLater(1, check_excite_activity, EXCITE_PAY_ACTIVITY)
            reactor.callLater(1, check_excite_activity, EXCITE_CONSUME_ACTIVITY)
            reactor.callLater(1, check_excite_activity, EXCITE_GROUP_BUY)
            reactor.callLater(1, worldBoss.init)
            print 'WARNING. e: ', e
            #print 'WARNING. Redis connection fail, callLater 1 second. redis:', redis
 
    def cleanup(self):
        pass

    def stopFactory(self):
        print '=============================\n'
        print '*  Game Server Stop!     *\n'
        print '============================='

        try:
            g_UserMgr.stop()
        except:
            log.exception()

    def connectGW(self):
        ReConnectCreator(self.GWConnectionMade, config.gw_host, config.gw_port).connect()

    @defer.inlineCallbacks
    def GWConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'gs')

            log.info('registedGW: result:%s, me:%s, peer:%s.' % (res, p.transport.getHost(), p.transport.getPeer()))
            if res[0] == 0:
                protocol_manager.set_server('gw', p)

    def connectCS(self):
        ReConnectCreator(self.CSConnectionMade, config.char_host, config.char_port).connect()

    @defer.inlineCallbacks
    def CSConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'gs')

            log.info('registedCS: result:%s, me:%s, peer:%s.' % (res, p.transport.getHost(), p.transport.getPeer()))
            if res[0] == 0:
                protocol_manager.set_server('cs', p)

    def connectMS(self):
        ReConnectCreator(self.MSConnectionMade, config.ms_host, config.ms_port).connect()

    @defer.inlineCallbacks
    def MSConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'gs')

            log.info('registedMS: result: {0}, me: {1}, peer: {2}.'.format( res, p.transport.getHost(), p.transport.getPeer() ))
            if res[0] == 0:
                protocol_manager.set_server('ms', p)

    def connectAlliance(self):
        ReConnectCreator(self.AllianceConnectionMade, config.alli_host, config.alli_port).connect()

    @defer.inlineCallbacks
    def AllianceConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'gs')

            log.info('registedAlliance: result: {0}, me: {1}, peer: {2}.'.format( res, p.transport.getHost(), p.transport.getPeer() ))
            if res[0] == 0:
                protocol_manager.set_server('alli', p)

