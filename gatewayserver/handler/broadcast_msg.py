#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


from rpc   import route
from redis import redis


from twisted.internet import defer
from log              import log
from constant         import *
from errorno          import NO_ERROR
from marshal          import loads, dumps


# 本地的走马灯内容
BROADCAST_MESSAGES = None

@route()
@defer.inlineCallbacks
def get_broadcast_messages(p, req):
    ''' 获取本地循环播放的走马灯消息 '''
    global BROADCAST_MESSAGES

    if BROADCAST_MESSAGES is not None:
        defer.returnValue( (NO_ERROR, BROADCAST_MESSAGES) )
    else:
        BROADCAST_MESSAGES = []

    _all_msgs = yield redis.hget( HASH_OSS_MESSAGES, FIELD_BROADCAST )
    if not _all_msgs:
        defer.returnValue( (NO_ERROR, []) )

    BROADCAST_MESSAGES = loads(_all_msgs)

    defer.returnValue( (NO_ERROR, BROADCAST_MESSAGES) )

def curr_broadcast_messages():
    return BROADCAST_MESSAGES

def sync_broadcast_messages(msgs):
    global BROADCAST_MESSAGES
    BROADCAST_MESSAGES = msgs

@route()
@defer.inlineCallbacks
def time_limited_shop_desc(p, req):
    ''' 获取限时商店中的说明 '''
    desc_msgs = yield redis.hget( HASH_OSS_MESSAGES, FIELD_LIMIT_SHOP_DESC )
    if not desc_msgs:
        defer.returnValue( (NO_ERROR, []) )

    desc_msgs = loads(desc_msgs)

    defer.returnValue( (NO_ERROR, [desc_msgs['title'], desc_msgs['content']]) )





