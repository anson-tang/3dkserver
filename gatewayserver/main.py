#!/usr/bin/env python
#-*-coding: utf-8-*-

from twisted.application     import internet, service
from twisted.internet        import reactor, protocol
from twisted.manhole.telnet  import ShellFactory
from twisted.web             import http
from twisted.python.log      import ILogObserver, FileLogObserver
from twisted.python.logfile  import LogFile

import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

from os.path import abspath, dirname, join, normpath
PREFIX = normpath(dirname(abspath(__file__)))
for path in (PREFIX, normpath(join(PREFIX, '../lib'))):
    if path not in sys.path:
        sys.path = [path] + sys.path

SERVER_NAME = 'GATEWAYSERVER'

import config
config.init(SERVER_NAME)
import log
log.init(config.log_threshold)

import redis
redis.init(config.redis_conf)

'''
from syslogger import init_logger
syslog_conf = config.syslog_conf.split(',')
if len(syslog_conf) > 1:
    syslog_conf = (syslog_conf[0], int(syslog_conf[1]))
else:
    syslog_conf = syslog_conf[0]
init_logger( syslog_conf )
'''
from server     import Server
from web.server import process
from datetime import datetime

server = Server()

httpserver = http.HTTPFactory()
httpserver.protocol().requestFactory.process = process
#httpserver.protocol.requestFactory.process = process

reactor.addSystemEventTrigger('before', 'shutdown', server.cleanup)

application = service.Application(SERVER_NAME)

log_path   = config.log_path
log_rotate = int(config.log_rotate_interval)
logfile    = LogFile('gateway.log', log_path, rotateLength=log_rotate)
logOb = FileLogObserver(logfile)
logOb.formatTime = lambda when : datetime.fromtimestamp(when).strftime('%m/%d %T.%f')

application.setComponent( ILogObserver, logOb.emit )

internet.TCPServer(config.port, server, backlog=500).setServiceParent(service.IServiceCollection(application))
internet.TCPServer(config.httport, httpserver).setServiceParent(service.IServiceCollection(application))
internet.TCPServer(config.adminport, ShellFactory(), interface='127.0.0.1').setServiceParent(service.IServiceCollection(application))
