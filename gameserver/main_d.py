#!/usr/bin/env python
#-*- coding: utf-8-*-

from twisted.application import internet, service
from twisted.internet import reactor, protocol
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
SERVER_NAME = 'GAMESERVER'
config.init(SERVER_NAME)
import log
log.init(config.conf)

from server import Server

@defer.inlineCallbacks
def test():
    from gscharacter import GSCharacter
    from gsfellow    import GSFellowManager
    from gsuser      import g_UserMgr

    c = GSCharacter(9527)
    c.syncCharacterToCS()
    _shrine = c.getShrine(1)
    _shrine = c.getShrine(2)
    _shrine = c.getShrine(3)

    gf = GSFellowManager(9527)
    #gf.addFellow(45, 1)

server = Server()
reactor.addSystemEventTrigger('before', 'shutdown', server.cleanup)
application = service.Application(SERVER_NAME)
internet.TCPServer(config.port, server, interface=config.interface).setServiceParent(service.IServiceCollection(application))
internet.TCPServer(config.adminport, ShellFactory(), interface=config.interface).setServiceParent(service.IServiceCollection(application))
