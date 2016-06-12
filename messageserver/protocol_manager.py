#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from twisted.internet import defer
from log import log

class ProtocolManager(object):
    def __init__(self):
        self.gw = None
        self.gs = None

    def set_server(self, server, p):
        if server == 'gw':
            self.gw = p
        elif server == 'gs':
            self.gs = p

    def gw_call():
        if self.gw:
            return self.gw.call(func, args)
        else:
            defer.fail(Exception('Error, gw not exists.'))

    def gs_call(self, func, args):
        if self.gs:
            return self.gs.call(func, args)
        else:
            return defer.fail(Exception('Error, gs not exists.'))

    def gw_send(self, cid, func, args):
        if self.gw:
            self.gw.send('sync2client', (cid, func, args))
        else:
            #return defer.fail(Exception('Error, gw not exists.'))
            log.exception('Error, gw not exists.')

    def gw_broadcast(self, func, args, cids):
        if self.gw:
            self.gw.send('room_broadcast', (func, args, cids))
        else:
            #return defer.fail(Exception('Error, gw not exists.'))
            log.exception('Error, gw not exists.')


protocol_manager = ProtocolManager()

gw_broadcast = protocol_manager.gw_broadcast
gw_send      = protocol_manager.gw_send



