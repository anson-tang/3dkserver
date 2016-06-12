#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rpc import route
from protocol_manager import protocol_manager
from manager.gateuser import g_UserMgr
from twisted.internet import reactor
from constant         import MAX_CLIENTS_BORADCAST_PER_LOOP


from log import log

@route()
def registersrv(p, req):
    server = req
    p.setTimeout( None )
    protocol_manager.set_server(server, p)
    return 0, 0

@route()
def sync2client(p, req):
    cid, func, args = req
    send2client(cid, func, args)

def send2client(cid, func, args):
    _user =g_UserMgr.getUserByCid( cid )
    if _user and _user.p:
        _user.p.send(func, args)
    else:
        log.warn( 'user ({0}) not found.'.format( cid ) )

@route()
def broadcast(p, req):
    func, args = req
    _remain = g_UserMgr.all_users()
    __broadcast(_remain, func, args)

@route()
def broadcast_with_cids(p, req):
    room_broadcast(p, req)

@route()
def room_broadcast(p, req):
    func, args, cids = req
    _remain = g_UserMgr.room_users( cids )
    __broadcast(_remain, func, args)

def __broadcast(user_remain, func, args):
    if user_remain:
        i = 0
        while i < MAX_CLIENTS_BORADCAST_PER_LOOP:
            i += 1
            _user = user_remain.pop( 0 )
            if _user:
                if hasattr(_user, 'p'):
                    if hasattr(_user.p, 'transport'):
                        if _user.p.transport:
                            _user.p.send(func, args)
                        else:
                            log.warn('__broadcast. cid:{0}, unknown t:{1}.'.format(_user.cid, _user.p.transport))
                            g_UserMgr.del_zombie_user( _user.cid )
                    else:
                        log.warn('__broadcast. cid:{0}, the p has no transport attribute..'.format(_user.cid))
                        g_UserMgr.del_zombie_user( _user.cid )
                else:
                    log.warn('__broadcast. cid:{0}, the user has no p attribute..'.format(_user.cid))
                    g_UserMgr.del_zombie_user( _user.cid )
            else:
                log.info('__broadcast. Unknown user.')

            if not user_remain:
                break
        else:
            reactor.callLater(1, __broadcast, user_remain, func, args)

