#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.internet import reactor, defer
from log import log


class ProtocolManager(object):
    def __init__(self):
        self.ls   = None
        self.gw   = None
        self.cs   = None
        self.ms   = None
        self.alli = None

    def set_server(self, server, p):
        if server == 'gw':
            self.gw = p
        elif server == 'ls':
            self.ls = p
        elif server == 'cs':
            self.cs = p
        elif server == 'ms':
            self.ms = p
        elif server == 'alli':
            self.alli = p

        log.debug('[ ProtocolManager ]server:%s, all:' % server, 'ls:', self.ls, 'gw:', self.gw, 'cs:', self.cs, 'ms:', self.ms)

    def gw_call(self, func, args):
        gw = self.gw
        if gw:
            return gw.call(func, args)
        else:
            return defer.fail(Exception('Error, gw not exists'))

    def gw_send(self, cid, func, args):
        if self.gw:
            self.gw.send('sync2client', (cid, func, args))
        else:
            log.exception('Error, gw not exists')

    def gw_broadcast(self, func, args):
        if self.gw:
            self.gw.send('broadcast', (func, args))
        else:
            log.exception('Error, gw not exists')

    def gw_broadcast_cids(self, func, args, recvers):
        if self.gw:
            self.gw.send('broadcast_with_cids', (func, args, recvers))
        else:
            log.exception('Error, gw not exists')

    def ls_call(self, func, args):
        ls = self.ls
        if ls:
            return ls.call(func, args)
        else:
            return defer.fail(Exception('Error, ls not exists'))

    def cs_call(self, func, args):
        cs = self.cs
        if cs:
            return cs.call(func, args)
        else:
            return defer.fail(Exception('Error, cs not exists'))

    def ms_call(self, func, args):
        if self.ms:
            return self.ms.call(func, args)
        else:
            return defer.fail(Exception('Error, ms not exists.'))

    def ms_send(self, func, args):
        if self.ms:
            self.ms.send(func, args)
        else:
            log.exception('Error, ms not exists.')

    def alli_call(self, func, args):
        if self.alli:
            return self.alli.call(func, args)
        else:
            return defer.fail(Exception('Error, alli not exists.'))

    def alli_send(self, func, args):
        if self.alli:
            self.alli.send(func, args)
        else:
            log.exception('Error, ms not exists.')

    def log_info(self, *a):
        self.ls_call('log_info', a)

    def kl_log(self, prefix, *a):
        self.ls_call('kl_log', [prefix] + a)


protocol_manager = ProtocolManager()
ms_call   = protocol_manager.ms_call
ms_send   = protocol_manager.ms_send
alli_call = protocol_manager.alli_call
alli_send = protocol_manager.alli_send
cs_call   = protocol_manager.cs_call
gw_call   = protocol_manager.gw_call
gw_send   = protocol_manager.gw_send
gw_broadcast = protocol_manager.gw_broadcast
gw_broadcast_cids = protocol_manager.gw_broadcast_cids

