#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet.protocol import ServerFactory
from twisted.internet import protocol, reactor, defer
from rpc import GeminiRPCProtocol, load_all_handlers
from os.path import abspath, dirname


import config
class Server(ServerFactory):
    protocol = GeminiRPCProtocol

    def startFactory(self):
        print '=============================\n'
        print '*   Character Server Start!   *\n'
        print '=============================', dirname(abspath(__file__)) + '/'
        load_all_handlers(dirname(abspath(__file__)) + '/', 'handler')

        #reactor.callLater(1, test)

    def cleanup(self):
        pass

    def stopFactory(self):
        print '=============================\n'
        print '*  Character Server Stop!     *\n'
        print '============================='

try:
    server
except NameError:
    server = Server()
