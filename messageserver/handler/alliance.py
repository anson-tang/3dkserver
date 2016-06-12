#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

from rpc              import route
from twisted.internet import defer

from log              import log
from errorno          import *
from constant         import *

from manager.messageuser  import g_UserMgr



@route()
def ms_alliance_info(p, req):
    ''' 同步玩家的公会信息 '''
    cid, alliance_info = req

    user = g_UserMgr.getUserByCid(cid)
    if user:
        user.update_alliance( alliance_info )

@route()
def ms_alliance_position(p, req):
    ''' 同步玩家的职位 '''
    cid, position = req

    user = g_UserMgr.getUserByCid(cid)
    if user:
        user.update_position( position )







