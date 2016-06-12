#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.application import internet, service
from twisted.internet import reactor, protocol, defer
from twisted.manhole.telnet import ShellFactory

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

from os.path import abspath, dirname, join, normpath
PREFIX = normpath(dirname(abspath(__file__)))
for path in (PREFIX, normpath(join(PREFIX, '../lib'))):
    if path not in sys.path:
        sys.path = [path] + sys.path

import config
SERVER_NAME = 'CHARACTERSERVER'
config.init(SERVER_NAME)
import log
log.init(config.conf)

from server import server

@defer.inlineCallbacks
def test():
    from manager.character import Character
    from manager.csuser    import g_UserMgr
    from manager.fellow    import Fellow 

    c = Character(50174)
    yield c.load()
    log.log.debug('[ test character ]:', c.value)
    if c.cid:
        c.register()
        
        fellow = Fellow(c.cid)
        yield fellow.load()

        _user = g_UserMgr.getUser( c.cid )
        if _user:
            fellow.register(_user)
            log.log.debug('[ fellow ]:registered.', fellow.keys())

reactor.addSystemEventTrigger('before', 'shutdown', server.cleanup)
reactor.callLater(2, test)
application = service.Application(SERVER_NAME)
internet.TCPServer(config.port+100, server, interface=config.interface).setServiceParent(service.IServiceCollection(application))
