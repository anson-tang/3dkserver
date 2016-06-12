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

@route()
@defer.inlineCallbacks
def jade_list(p, req):
    ''' 获取玉魄列表 '''
    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    _len, value_list = yield user.bag_jade_mgr.value_list( index )
    max_capacity     = user.base_att.jade_capacity
    _level           = user.bag_jade_mgr.random_jade_level
    defer.returnValue( (_len, max_capacity, _level, value_list) )

@route()
@defer.inlineCallbacks
def random_jade(p, req):
    ''' 鉴玉 '''
    cid, [random_times] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    _cur_capacity = yield user.bag_jade_mgr.cur_capacity()
    if _cur_capacity >= user.base_att.jade_capacity:
        defer.returnValue( JADE_CAPACITY_NOT_ENOUGH )

    res_err = yield user.bag_jade_mgr.random_new_jade( random_times )
    # 开服七天
    yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_15, random_times)
    yield user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_15, random_times)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def upgrade_random_jade_level(p, req):
    ''' 召唤宝玉 '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    if JADE_UPGRADE_LEVEL <= user.bag_jade_mgr.random_jade_level:
        defer.returnValue( JADE_UPGRADE_LEVEL_ERROR )

    res_err = yield user.bag_jade_mgr.upgrade_random_level()
    # 开服七天
    yield user.open_server_mgr.update_open_server_activity_quest( OPEN_SERVER_QUEST_ID_15, 1)
    yield user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_15, 1)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def jade_strengthen(p, req):
    ''' 升级玉魄 '''
    cid, [user_jade_id, jades_data] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    if not jades_data:
        defer.returnValue( CLIENT_DATA_ERROR )

    res_err = yield user.bag_jade_mgr.strengthen(user_jade_id, jades_data)

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_camp_jade(p, req):
    ''' 新增、更换阵容中的玉魄 '''
    cid, [camp_id, pos_id, old_ujid, new_ujid] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    if not new_ujid:
        defer.returnValue( CLIENT_DATA_ERROR )
    elif old_ujid: # 更换
        res_err = yield user.bag_jade_mgr.jade_replace( camp_id, pos_id, old_ujid, new_ujid )
    else: # 新增
        res_err = yield user.bag_jade_mgr.jade_wear( camp_id, pos_id, new_ujid )
 
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_jade_one_touch(p, req):
    ''' 一键穿戴玉魄 '''
    cid, [camp_id, one_touch_data] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.bag_jade_mgr.set_one_touch( camp_id, one_touch_data )
    defer.returnValue( res_err )










