#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.internet import reactor, defer


class ProtocolManager(object):
    def __init__(self):
        self.ls = None
        self.gs = None

    def set_server(self, server, p):
        if server == 'gs':
            self.gs = p
        elif server == 'ls':
            self.ls = p

    def gs_call(self, func, args):
        gs = self.gs
        if gs:
            return gs.call(func, args)
        else:
            return defer.fail(Exception('Error, gs not exists'))

    def ls_call(self, func, args):
        ls = self.ls
        if ls:
            return ls.call(func, args, callback)
        else:
            return defer.fail(Exception('Error, ls not exists'))

    def log_info(self, *a):
        self.ls_call('log_info', a)

    def kl_log(self, prefix, *a):
        self.ls_call('kl_log', [prefix] + a)


protocol_manager = ProtocolManager()

gs_call = protocol_manager.gs_call
