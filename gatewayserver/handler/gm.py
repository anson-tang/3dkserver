#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import reactor, defer

from rpc      import route
from .gs      import broadcast
from log      import log
from setting  import need_switch
from os       import system
from redis    import redis
from constant import SET_GM_USER

import time

opened         = not need_switch
time_will_stop = 0

def stop_real():
    system('./stop_real')
    log.warn( '[ stop_real ] opened:', opened )
    #reactor.stop()

def open_server():
    global opened, time_will_stop

    opened = True
    log.warn( '[ open_server ] opened:', opened )

def begin_stopping_server( seconds ):
    global opened, time_will_stop

    opened = False

    if seconds:
        broadcast( None, ( 'sync_server_stop', seconds ) )
        time_will_stop = time.time() + seconds + 3
        reactor.callLater( seconds + 3, stop_real )

    log.warn( '[ begin_stopping_server ]opened:', opened, 'seconds:', seconds, 'time_will_stop', time_will_stop )

@route()
def gm_server_status( p, req ):
    _host = p.transport.getPeer().host
    res = 0, 0


    if _host == '127.0.0.1':
        _n = time.time()
        res = opened, int( time_will_stop - _n )
        log.warn( '[ gm_server_status]:', opened, time_will_stop, _n, res )
    else:
        log.warn( '[ gm_server_status]:', req, p.transport.getPeer().host )

    return res

@route()
@defer.inlineCallbacks
def gm_add_admin_user( p, req ):
    _host = p.transport.getPeer().host
    res = 0, 0

    if _host == '127.0.0.1':
        _added = yield redis.sadd(SET_GM_USER, *req )
        log.warn( '[ gm_add_admin_user ]:', p.transport.getPeer().host, 'req:', req, 'added:', _added )

        res = 1, 1
    else:
        log.error( '[ gm_add_admin_user ]:', p.transport.getPeer().host, 'req:', req )

    defer.returnValue( res )

@route()
def gm_server_status_switch( p, req ):
    _host = p.transport.getPeer().host

    res = 0, 0

    if _host == '127.0.0.1':
        log.warn( '[ gm_server_status_switch ]:', req, p.transport.getPeer().host )

        _switch_on, _seconds_to_stop = req
        if _switch_on:
            open_server()
            res = 1, 1
        else:
            begin_stopping_server( _seconds_to_stop )
    else:
        log.error( '[ gm_server_status_switch ]:', req, p.transport.getPeer().host )

    return res
