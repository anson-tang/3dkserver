#-*-coding: utf-8 -*-

from twisted.internet import reactor, protocol, defer
from twisted.internet.protocol import _InstanceFactory, ReconnectingClientFactory, ClientCreator
from rpc import GeminiRPCProtocol
from log import log


class _ReconnectInstanceFactory(ReconnectingClientFactory):
    def __init__(self, protocolClass, creator):
        self.protocol = protocolClass
        self.creator = creator

    def buildProtocol(self, addr):
        p = ReconnectingClientFactory.buildProtocol(self, addr)
        print 'p:', p
        reactor.callLater(0, self.creator.callback, p)
        self.retries = 0
        self.delay = self.initialDelay
        self.factor = 1.6180339887498948
        return p

    def loseConnection(self, sessionid):
        pass


class ReConnectCreator(protocol.ClientCreator):
    def __init__(self, handler, host, port, *args, **kwargs):
        self.connectedHandler = handler
        self.server_host      = host
        self.server_port      = port

        protocol.ClientCreator.__init__(self, reactor, GeminiRPCProtocol, *args, **kwargs)

    def _connect(self, method, *args, **kwargs):
        def cancelConnect(deferred):
            connector.disconnect()
            if f.pending is not None:
                f.pending.cancel()
        d = defer.Deferred(cancelConnect)
        f = _ReconnectInstanceFactory(
            self.protocolClass, self)
        connector = method(factory=f, *args, **kwargs)
        return d

    def connect(self, timeout = 10):
        return self.connectTCP(self.server_host, self.server_port, timeout).addCallbacks(self.callback, self.errback)

    def callback(self, p):
        p.server_host = self.server_host
        p.server_port = self.server_port
        self.connectedHandler(p)

    def errback(self, error):
        print '[ReConnectCreator]connect failed. service:', 'reason:', reason.getErrorMessage()
        return error
