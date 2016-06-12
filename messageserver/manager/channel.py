#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import Queue

from log                  import log
from twisted.internet     import reactor
from protocol_manager     import gw_broadcast
from constant             import CHAT_MSG_LOGOUT_MAX_LEN, CHAR_MSG_BROADCAST_MAX_LEN, CHAT_BROADCAST_INTERVAL, CHAT_MSG_QUEUE_MAX_LEN
from errorno              import UNKNOWN_ERROR, NO_ERROR, CONNECTION_LOSE
from manager.messageuser  import g_UserMgr


class Channel(object):
    def __init__(self):
        self.__msg_id    = 0
        self.__last_msgs = []
        self.msgs        = Queue.Queue(CHAT_MSG_QUEUE_MAX_LEN)

        self.channel = 1
        self.broadcast_protocol = 'channel_broadcast'
        reactor.callLater(CHAT_BROADCAST_INTERVAL, self.broadcast)

    def last_msgs(self):
        return self.__last_msgs

    def new_msg(self, user, content):
        '''
        @param mgs-[msg_id, sender_cid, lead_id, nick_name, vip_level, content]
        '''
        self.__msg_id = self.__msg_id if self.__msg_id < 2**32-1 else 1
        self.__msg_id += 1

        _msg = (self.__msg_id, user.cid, user.lead_id, user.nick_name, user.vip_level, content, user.level, user.might, user.position)
        self.msgs.put( _msg )

        self.__last_msgs.append( _msg )
        if len(self.__last_msgs) > CHAT_MSG_LOGOUT_MAX_LEN:
            del self.__last_msgs[0]

        return [self.__msg_id]

    def broadcast(self):
        _len = self.msgs.qsize()
        if _len > 0:
            _count = min(_len, CHAR_MSG_BROADCAST_MAX_LEN)

            i = 0
            _msgs = []
            while i < _count:
                i += 1
                try:
                    _msgs.append( self.msgs.get_nowait() )
                except Queue.Empty:
                    break
                except Exception as e:
                    log.error( "Broadcast error. e: %s." % ( e ))
            cids_in_room, cids_notice = g_UserMgr.getBroadcastCids()
            #log.info('For Test. cids_in_room: {0}, cids_notice: {1}.'.format( cids_in_room, cids_notice ))
            if cids_in_room and _msgs:
                gw_broadcast(self.broadcast_protocol, _msgs, cids_in_room)
            if cids_notice and _msgs:
                g_UserMgr.updateNotifyFlag( cids_notice )
                gw_broadcast('new_chat_message', [self.channel], cids_notice)

        reactor.callLater(CHAT_BROADCAST_INTERVAL, self.broadcast)


class Alliance(Channel):
    def __init__(self, alliance_id):
        Channel.__init__(self)
        self.channel = 3
        self.alliance_id = alliance_id
        self.broadcast_protocol = 'alliance_broadcast'

    def broadcast(self):
        _len = self.msgs.qsize()
        if _len > 0:
            _count = min(_len, CHAR_MSG_BROADCAST_MAX_LEN)

            i = 0
            _msgs = []
            while i < _count:
                i += 1
                try:
                    _msgs.append( self.msgs.get_nowait() )
                except Queue.Empty:
                    break
                except Exception as e:
                    log.error( "Broadcast error. e: %s." % ( e ))
            cids_in_room, cids_notice = g_UserMgr.getAllianceCids(self.alliance_id)
            #log.info('For Test. cids_in_room: {0}, cids_notice: {1}.'.format( cids_in_room, cids_notice ))
            if cids_in_room and _msgs:
                gw_broadcast(self.broadcast_protocol, _msgs, cids_in_room)
            if cids_notice and _msgs:
                g_UserMgr.updateNotifyFlag( cids_notice )
                gw_broadcast('new_chat_message', [self.channel], cids_notice)

        reactor.callLater(CHAT_BROADCAST_INTERVAL, self.broadcast)

g_Channel  = Channel()

