#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import Queue

from log                  import log
from twisted.internet     import reactor
from protocol_manager     import gw_send
from constant             import CHAT_MSG_LOGOUT_MAX_LEN, CHAR_MSG_BROADCAST_MAX_LEN, CHAT_BROADCAST_INTERVAL, CHAT_MSG_QUEUE_MAX_LEN
from errorno              import UNKNOWN_ERROR, NO_ERROR, CONNECTION_LOSE
from manager.messageuser  import g_UserMgr


class Private(object):
    def __init__(self):
        self.__msg_id_dic    = {}
        self.__last_msgs_dic = {}

    def last_msgs(self, cid):
        return self.__last_msgs_dic.get( cid, [] )

    def new_msg(self, user, rcv_user, content):
        '''
        @param mgs-[msg_id, sender_cid, lead_id, nick_name, vip_level, content]
        '''
        rcv_msg_id = self.__msg_id_dic.setdefault(rcv_user.cid, 1) + 1
        rcv_msg_id = rcv_msg_id if rcv_msg_id < 2**32-1 else 1

        self.__msg_id_dic[rcv_user.cid] = rcv_msg_id

        rcv_msg = [rcv_msg_id, user.cid, user.lead_id, user.nick_name, user.vip_level, content, user.level, user.might, user.position]
        rcv_last_msgs = self.__last_msgs_dic.setdefault( rcv_user.cid, [] )
        rcv_last_msgs.append( rcv_msg )
        if len(rcv_last_msgs) > CHAT_MSG_LOGOUT_MAX_LEN:
            del rcv_last_msgs[0]

        # 发送者的历史消息维护
        msg_id = self.__msg_id_dic.setdefault(user.cid, 1) + 1
        msg_id = msg_id if msg_id < 2**32-1 else 1
        self.__msg_id_dic[user.cid] = msg_id
        msg    = [msg_id, user.cid, user.lead_id, user.nick_name, user.vip_level, content, user.level, user.might, user.position]

        last_msgs = self.__last_msgs_dic.setdefault( user.cid, [] )
        last_msgs.append( msg )
        if len(last_msgs) > CHAT_MSG_LOGOUT_MAX_LEN:
            del last_msgs[0]

        if rcv_user.in_room:
            gw_send(rcv_user.cid, 'private_forward_to', rcv_msg)
        elif not rcv_user.notice_flag:
            g_UserMgr.updateNotifyFlag( [rcv_user.cid] )
            gw_send(rcv_user.cid, 'new_chat_message', [2])

        return [msg_id]

g_Private = Private()
