#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from rpc      import route
from errorno  import *
from constant import *
from twisted.internet     import defer

from manager.messageuser  import g_UserMgr


@route()
@defer.inlineCallbacks
def sync_char_data(p, req):
    ''' _type: 1-nick_name, 2-lead_id, 3-vip_level, 4-level, 5-might '''
    cid, _type, _value = req

    user = g_UserMgr.getUserByCid(cid)
    if user:
        if _type == SYNC_NICK_NAME:
            user.rename( _value )
        elif _type == SYNC_LEAD_ID:
            user.update_lead_id( _value )
        elif _type == SYNC_VIP_LEVEL:
            user.update_vip_level( _value )
        elif _type == SYNC_LEVEL:
            user.update_level( _value )
        elif _type == SYNC_MIGHT:
            yield user.update_might( _value )

@route()
def revise_name(p, req):
    cid, new_name = req
    user = g_UserMgr.getUserByCid(cid)
    if user:
        user.rename(new_name)
        g_UserMgr.revise_dict_user_name(cid, new_name)
