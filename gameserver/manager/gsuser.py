#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author:
# License: 
# Summary: 


from time     import time
from log      import log
from errorno  import *
from constant import *

from twisted.internet    import reactor,defer

class GSUserMgr(object):
    def __init__(self):
        self.__dic_uid_user = {}#k:uid v:user

    def online_status(self, cid):
        '''
        @return: True-online, False-offline.
        '''
        _status = False
        user = self.__dic_uid_user.get( cid, None )
        if user and (not user.offline_flag):
            _status = True

        return _status

    @property
    def online_cnt(self):
        ''' used to query. '''
        return len(self.__dic_uid_user)

    def online_cids(self):
        ''' used to query, include offline login. '''
        return self.__dic_uid_user.keys()

    def offline_cids(self, flag=False):
        ''' used to query. 
        @param: flag-返回离线登陆玩家详情的标志位
        '''
        _cids = []
        for user in self.__dic_uid_user.itervalues():
            if user and user.offline_flag:
                _cids.append( (user.cid, user.offline_num) )

        if flag:
            return len(_cids), _cids
        else:
            return len(_cids), []

    def stop(self):
        for user in self.__dic_uid_user.itervalues():
            if user:
                user.logout()

    def logoutUser(self, cid):
        if cid not in self.__dic_uid_user:
            log.debug('Can not find user. cid:', cid)
            return

        user = self.__dic_uid_user[cid]
        if user.offline_num > 1:
            log.debug('Had offline login user. offline_num: {0}.'.format( user.offline_num ))
            return

        user.logout()
        del self.__dic_uid_user[cid]

    def kickoutUser(self, cid):
        if cid not in self.__dic_uid_user:
            return

        user = self.__dic_uid_user[cid]
        if user.offline_num > 1:
            user.offline_num = 0

        user.logout()
        del self.__dic_uid_user[cid]

    def getUser(self, cid, flag=False):
        user = self.__dic_uid_user.get( cid, None )
        if user and flag: # flag=True 离线登陆的标志位
            user.offline_num += 1
        return user

    def getUserByLevel(self, start_level, end_level, except_ids):
        users = []
        for user in self.__dic_uid_user.itervalues():
            if not user or user.cid in except_ids:
                continue
            if user.level >= start_level and user.level <= end_level:
                users.append( user )
        return users

    def loginUser(self, char_data, flag=False):
        '''
        @param: char_data=[id, account, nick_name, ...]
        @param: flag-离线登陆的标志位
        '''
        from manager.gscharacter import GSCharacter
        char_data = dict(zip(GSCharacter._fields, char_data))

        cid  = char_data['id']
        user = self.getUser(cid, flag)

        if user:
            log.error('user had exists already. cid {0}.'.format(cid))
            return user

        user = GSCharacter(cid)

        self.__dic_uid_user[cid] = user
        user.load( char_data, flag )
        # 离线登陆的标志位
        if flag: 
            user.offline_num += 1

        log.debug('load user data. cid: {0}'.format( cid ))
        return user

g_UserMgr = GSUserMgr()
