#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2015 Don.Li
# Summary: 

from rpc      import route
from log      import log
from errorno  import *
from constant import *

from twisted.internet import defer
from manager.gsuser   import g_UserMgr

from models.worldboss import AttackerData, worldBoss, BOOST_EXTRA_PER_LEVEL
from protocol_manager import gw_broadcast

@route()
@defer.inlineCallbacks
def worldboss_status(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        _status    = None
        _boss_life = 0

        if worldBoss.running:
            _attacker  = yield AttackerData.get(cid)
            if _attacker:
                _status = yield _attacker.value
            else:
                log.error('have no attacker data generated. cid:', cid)

            _boss_life = worldBoss.life

        res = worldBoss._duration, worldBoss._level, worldBoss.value, _status, _boss_life, BOOST_EXTRA_PER_LEVEL

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def worldboss_enter(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        _boss_life = 0
        _status    = None

        if worldBoss.running:
            _attacker = yield AttackerData.get(cid)
            if _attacker:
                _status = yield _attacker.value
            else:
                log.error('have no attacker data generated. cid:', cid)

            _boss_life = worldBoss.life
            res = _status, _boss_life
        else:
            res = WORLDBOSS_NOT_RUNNING

    defer.returnValue( res )

@route()
def worldboss_leave(p, req):
    res = NO_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user and worldBoss.running:
        worldBoss.remove_attacker(cid)

    return res

@route()
@defer.inlineCallbacks
def worldboss_attack(p, req):
    res = UNKNOWN_ERROR

    cid, (damage, )= req

    user = g_UserMgr.getUser(cid)
    if user:
        if worldBoss.running:
            _attacker = yield AttackerData.get(cid)
            if _attacker:
                res, report = yield _attacker.attack( user, damage )
                user.achievement_mgr.update_achievement_status(ACHIEVEMENT_QUEST_ID_21, 1) 
                if not res:
                    res = report
        else:
            res = WORLDBOSS_NOT_RUNNING

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def worldboss_clear_cd(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        if worldBoss.running:
            _attacker = yield AttackerData.get(cid)
            if _attacker:
                res = _attacker.clear_cd(user)
                if not res:
                    res = _attacker._clear_count, user.credits
        else:
            res = WORLDBOSS_NOT_RUNNING

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def worldboss_boost(p, req):
    res = UNKNOWN_ERROR

    cid, (boost_type, ) = req

    user = g_UserMgr.getUser(cid)
    if user:
        if worldBoss.running:
            _attacker = yield AttackerData.get(cid)
            if _attacker:
                res = _attacker.boost(user, boost_type)
                if not res:
                    res = _attacker._gold_inspire_success_count, _attacker._credit_inspire_success_count, user.golds, user.credits
        else:
            res = WORLDBOSS_NOT_RUNNING

    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def worldboss_attacked_rank(p, req):
    res = UNKNOWN_ERROR

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        res = yield worldBoss.current_rank()

    defer.returnValue( res )
