#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import config

from twisted.internet.protocol  import ServerFactory
from twisted.internet           import reactor, defer
from rpc                        import GeminiRPCProtocol, load_all_handlers
from os.path                    import abspath, dirname
from reconnect                  import ReConnectCreator
from protocol_manager           import protocol_manager


class Server(ServerFactory):
    protocol = GeminiRPCProtocol

    def startFactory(self):
        print '=============================\n'
        print '*   Message Server Start!   *\n'
        print '=============================', dirname(abspath(__file__)) + '/'
        load_all_handlers(dirname(abspath(__file__)) + '/', 'handler')

        self.connectGW()

    def cleanup(self):
        pass

    def stopFactory(self):
        print '=============================\n'
        print '*  Message Server Stop!     *\n'
        print '============================='

    def connectGW(self):
        ReConnectCreator(self.GWConnectionMade, config.gw_host, config.gw_port).connect()

    @defer.inlineCallbacks
    def GWConnectionMade(self, p):
        if p is None:
            reactor.stop()
        else:
            p.setTimeout( None )
            res = yield p.call('registersrv', 'ms')
            
            print ('registedGW: result:%s, me:%s, peer:%s.' % (res, p.transport.getHost(), p.transport.getPeer()))
            if res[0] == 0:
                protocol_manager.set_server('gw', p)


try:
    server
except NameError:
    server = Server()


