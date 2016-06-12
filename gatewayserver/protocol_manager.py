#!/usr/bin/env python
#-*-coding: utf-8-*-
from twisted.internet import reactor, defer


class ProtocolManager(object):
    def __init__(self):
        self.ls   = None
        self.gs   = None
        self.ms   = None
        self.alli = None

    def set_server(self, server, p):
        if server == 'gs':
            self.gs = p
        elif server == 'ls':
            self.ls = p
        elif server == 'ms':
            self.ms = p
        elif server == 'alli':
            self.alli = p

    def gs_call(self, func, args):
        gs = self.gs
        if gs:
            return gs.call(func, args)
        else:
            return defer.fail(Exception('Error, gs not exists'))

    def gs_send(self, func, args):
        if self.gs:
            self.gs.send(func, args)
        else:
            log.exception('Error, gs not exists.')

    def ms_call(self, func, args):
        if self.ms:
            return self.ms.call(func, args)
        else:
            return defer.fail(Exception('Error, ms not exists.'))

    def alli_call(self, func, args):
        if self.alli:
            return self.alli.call(func, args)
        else:
            return defer.fail(Exception('Error, alli not exists.'))

    def ls_call(self, func, args):
        ls = self.ls
        if ls:
            return ls.call(func, args)
        else:
            return defer.fail(Exception('Error, ls not exists'))

    def log_info(self, *a):
        self.ls_call('log_info', a)

    def kl_log(self, prefix, *a):
        self.ls_call('kl_log', [prefix] + a)


protocol_manager = ProtocolManager()
gs_call   = protocol_manager.gs_call
ms_call   = protocol_manager.ms_call
alli_call = protocol_manager.alli_call

gs_send   = protocol_manager.gs_send


