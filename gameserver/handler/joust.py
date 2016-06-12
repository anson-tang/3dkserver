#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


from rpc      import route
from log      import log
from errorno  import *
from constant import *


from twisted.internet import defer
from manager.gsuser   import g_UserMgr
from models.joust     import g_JoustMgr




@route()
@defer.inlineCallbacks
def get_joust_info(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.joust_info( user )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def refresh_joust_players(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.refresh_players( user )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def sync_joust_battle(p, req):
    cid, [position, battle_status] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.request_joust_battle( JOUST_BATTLE_NORMAL, user, position, battle_status )
    rank = g_JoustMgr.get_char_rank(cid)
    user.achievement_mgr.update_achievement_status(19, rank)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_joust_ranklist(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.ranklist()

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_joust_enemy(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.enemy_info( user )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def sync_joust_revenge(p, req):
    cid, [enemy_cid, battle_status] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.request_joust_battle( JOUST_BATTLE_REVERGE, user, enemy_cid, battle_status )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def buy_joust_count(p, req):
    cid, [buy_count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    if buy_count <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res_err = yield g_JoustMgr.buy_battle_count( user, buy_count )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def honor_exchange_status(p, req):
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_JoustMgr.get_exchange_status( user )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def honor_exchange(p, req):
    cid, [exchange_id, exchange_count] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    if exchange_count <= 0:
        defer.returnValue( REQUEST_LIMIT_ERROR )

    res_err = yield g_JoustMgr.exchange_items( user, exchange_id, exchange_count )

    defer.returnValue( res_err )


