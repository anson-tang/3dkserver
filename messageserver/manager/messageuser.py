#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from log   import log


class MessageUser(object):
    ''' message server user manager
    '''
    def __init__(self, cid, nick_name, lead_id, vip_level, level, might, alliance_info):
        self.__cid       = cid
        self.__nick_name = nick_name
        self.__lead_id   = lead_id
        self.__vip_level = vip_level
        self.__level     = level
        self.__might     = might

        self.__alliance_id   = alliance_info[0]
        self.__alliance_name = alliance_info[1]
        self.__position  = alliance_info[2]

        self.in_room     = False # True-聊天       在房间中
        self.notice_flag = False # True-聊天新消息 已通知
        self.notify_mail = False # True-邮件       已通知

    @property
    def cid(self):
        return self.__cid

    @property
    def lead_id(self):
        return self.__lead_id

    @property
    def nick_name(self):
        return self.__nick_name

    @property
    def vip_level(self):
        return self.__vip_level

    @property
    def level(self):
        return self.__level

    @property
    def might(self):
        return self.__might

    @property
    def alliance_id(self):
        return self.__alliance_id

    @property
    def position(self):
        return self.__position

    def rename(self, new_name):
        ''' 修改昵称 '''
        self.__nick_name = new_name

    def update_alliance(self, alliance_info):
        ''' 更换公会 '''
        self.__alliance_id   = alliance_info[0]
        self.__alliance_name = alliance_info[1]
        self.__position = alliance_info[2]

    def update_position(self, position):
        ''' 更新公会中的职位 '''
        self.__position = position

    def update_vip_level(self, vip_level):
        ''' 更新vip 等级 '''
        self.__vip_level = vip_level

    def update_lead_id(self, lead_id):
        ''' 升级主角 '''
        self.__lead_id = lead_id

    def update_level(self, level):
        ''' 等级提升 '''
        self.__level = level

    def update_might(self, might):
        ''' 战力提升 '''
        self.__might = might if might > 0 else 0

class MessageUserMgr(object):
    def __init__(self):
        self.__user_dic = {}
        self.__alliance_dic = {}

    def getUserByCid(self, cid):
        return self.__user_dic.get(cid, None)
    
    def revise_dict_user_name(self, cid, new_name):
        if self.__user_dic.has_key(cid):
            self.__user_dic[cid].rename(new_name)

    def getBroadcastCids(self):
        cids_in_room, cids_notice = [], []
        for cid, user in self.__user_dic.iteritems():
            if user.in_room:
                cids_in_room.append( cid )
            elif not user.notice_flag:
                cids_notice.append( cid )

        return cids_in_room, cids_notice

    def getAlliance(self, alliance_id):
        if alliance_id <= 0:
            return None

        return self.__alliance_dic.get(alliance_id, None)

    def addAlliance(self, alliance):
        self.__alliance_dic[alliance.alliance_id] = alliance

    def getAllianceIds(self):
        return self.__alliance_dic.keys()

    def getAllianceCids(self, alliance_id):
        cids_in_room, cids_notice = [], []
        for cid, user in self.__user_dic.iteritems():
            if alliance_id != user.alliance_id:
                continue
            if user.in_room:
                cids_in_room.append( cid )
            elif not user.notice_flag:
                cids_notice.append( cid )

        return cids_in_room, cids_notice


    def updateNotifyFlag(self, cids):
        ''' 更新聊天新消息 通知的标志位 '''
        for cid in cids:
            user = self.__user_dic.get(cid, None)
            if user:
                user.notice_flag = True

    def login(self, cid, nick_name, lead_id, vip_level, level, might, alliance_info):
        _user = self.__user_dic.get(cid, None)
        if not _user:
            _user = MessageUser(cid, nick_name, lead_id, vip_level, level, might, alliance_info)
            self.__user_dic[cid] = _user

        return _user

    def logout(self, cid):
        _user = self.__user_dic.get(cid, None)
        if _user:
            del self.__user_dic[cid]
        else:
            log.error( "Unknown user. cid: {0}.".format( cid ))


g_UserMgr = MessageUserMgr()
