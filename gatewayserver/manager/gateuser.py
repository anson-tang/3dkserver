#!/usr/bin/env python
#-*-coding: utf-8-*-

from time             import time
from twisted.internet import reactor, defer
from constant import *
from errorno  import *
from log import log
from protocol_manager import gs_call, ms_call, alli_call

class GateUser(object):
    '''
    @summary: ...
    @param temp_lost:True-offline, False-online. used to 5min check. when it's status is False, don't kick it.
    '''
    def __init__(self, cid, account, info):
        self.cid = cid
        self.account = account
        self.session_key = ''
        self.info = info
        self.p = None
        #If user login or reconnect failure, set it to True!
        self.temp_lost = False
        # user logout's end timestamp, set a flag one-to-one of reactor logoutUserReal. 
        self.logout_timestamp = 0

class GateUserMgr(object):
    def __init__(self):
        self.user_dic = {} #Key is cid
        self.account_dic = {}#Key is account
        #self.nick_dic = {}#Key is nick
        # 同时在线的最高人数
        self.max_cnt = 0

    @property
    def online_cnt(self):
        ''' used to query. '''
        return len(self.user_dic)

    def online_cids(self):
        ''' used to query. '''
        return self.user_dic.keys()

    def connect_cids(self):
        ''' 保持连接的玩家id列表 '''
        _cids = []
        for _user in self.user_dic.values():
            if (not _user.temp_lost):
                _cids.append( _user.cid )
        return _cids

    def all_users(self):
        '''
        @summary: 返回temp_lost为False即还在线的在线玩家,用于广播, 其中不含五分钟的玩家, 
        '''
        online_users = []
        for _user in self.user_dic.values():
            if (not _user.temp_lost):
                online_users.append( _user )
        return online_users

    def room_users(self, cids):
        ''' 部分玩家信息
        '''
        _room_users = []
        for cid in cids:
            _user = self.user_dic.get( cid, None )
            if _user and (not _user.temp_lost):
                _room_users.append( _user )
        return _room_users

    def addUserByCid(self, user):
        if 0 != user.cid:
            if user.cid in self.user_dic:
                return False
            self.user_dic[user.cid] = user
            # 更新最高同时在线人数
            _total = len(self.user_dic)
            if _total > self.max_cnt:
                self.max_cnt = _total
            return True

    def addUserByAccount(self, user):
        self.account_dic[user.account] = user
        return True

    #def addUserByNick(self, nick, user):
    #    self.nick_dic[nick] = user
    #    return True

    def getUserByCid(self, cid):
        if cid in self.user_dic:
            return self.user_dic[cid]
        else:
            return None

    def getUserByAccount(self, account):
        if account in self.account_dic:
            return self.account_dic[account]
        else:
            return None

    #def getUserByNick(self, nick):
    #    if nick in self.nick_dic:
    #        return self.nick_dic[nick]
    #    else:
    #        return None

    def delUserByCid(self, cid):
        user = self.user_dic.get(cid, None)
        if user:
            del self.user_dic[cid]
            if user.account in self.account_dic:
                del self.account_dic[user.account]
            return True
        else:
            return False

    def delUserByAccount(self, account):
        user = self.account_dic.get(account, None)
        if user:
            del self.account_dic[account]
            if user.cid in self. user_dic:
                del self.user_dic[user.cid]
            return True
        else:
            return False

    def getUserLogined(self, cid, p, session_key, info={}):
        user = self.user_dic.get(cid, None)
        if user:
            if hasattr(user, 'p') and user.p and user.p.transport:
                try:
                    user.p.send('invalid_connect', None)
                    user.p.lose_connect = False
                    user.p.transport.loseConnection()
                except Exception, e:
                    log.error('exception. cid: {0}, e: {1}.'.format( cid, e ))

            user.p           = p
            p.cid            = user.cid
            user.session_key = session_key
            user.temp_lost   = False
            user.logout_timestamp = 0
            if info:
                user.info = info
            log.warn('Replace old client. cid: {0}.'.format( p.cid ))

        return user

    def loginUser(self, p, cid, sk, account, char_info):
        user = None
        if cid in self.user_dic:
            user = self.user_dic[cid]
        else:
            user = GateUser(cid, account, char_info)
        user.p = p
        user.session_key = sk

        p.cid = cid
        log.debug('cid {0}, account {1}'.format( cid, account ))
        user.account = account
        user.temp_lost = False
        user.logout_timestamp = 0

        if account:
            self.addUserByAccount(user)
        if cid != 0:
            self.addUserByCid(user)

        #nick =char_info['nick_name']
        #if nick and len(nick) > 0:
        #    self.addUserByNick(nick, user)
        #else:
        #    log.error('User nick is empty! cid:', cid)

    def logoutUser(self, cid):
        user = self.user_dic.get(cid, None)

        if user:
            user.p = None
            user.temp_lost = True
            # update logout_timestamp
            now_timestamp  = int(time())
            user.logout_timestamp = now_timestamp
 
            gs_call('sync_user_to_cs', cid)
            reactor.callLater(SESSION_LOGOUT_REAL,  self.logoutUserReal, cid, now_timestamp)
            log.debug('user will logout later. cid: {0}.'.format( cid ))
        else:
            log.warn('Unknown user. cid: {0}.'.format( cid ))

    def reconnectUser(self, p, cid, session_key):
        user = self.user_dic.get(cid, None)
        if user:
            if  user.session_key != session_key:
                log.error('Session not match. old sk: {0}, new sk:{1}.'.format( user.session_key, session_key ))
                return RECONNECT_FAIL
            #if False == user.temp_lost:
            #    log.error('It is not temp lost client. cid:', user.cid)
            #    return CONNECTION_LOSE

            # check old protocol is valid or not.
            old_p = user.p
            user.p = None
            if old_p:
                old_p.lose_connect = True
                if hasattr(old_p, 'cid') and old_p.cid:
                    old_p.cid = 0
                if old_p.transport:
                    old_p.transport.loseConnection()

            user.p = p
            user.temp_lost = False
            user.logout_timestamp = 0

            p.cid = user.cid
            p.account = user.account
            p.session_key = user.session_key

            log.info('Reconnect ok. cid: {0}, lose_connect: {1}.'.format( p.cid, p.lose_connect ))
            return NO_ERROR
        else:
            log.error('Can not find cid: {0}.'.format( cid ))
            return CONNECTION_LOSE

    @defer.inlineCallbacks
    def logoutUserReal(self, cid, now_timestamp):
        ''' 同时满足两个条件才能真正的删除玩家
           1: temp_lost == True, offline
           2: logout_timestamp == now_timestamp, 借用时间戳作为标识, 匹配后标识是同一个事件
        '''
        user = self.user_dic.get(cid, None)
        if user:
            log.debug('logout cid: {0}, temp_lost: {1}, logout_timestamp: {2}, now_timestamp: {3}.'.format(\
                    cid, user.temp_lost, user.logout_timestamp, now_timestamp) )
            if user.temp_lost and user.logout_timestamp == now_timestamp:
                self.delUserByCid( cid )
                gs_call('gs_logout', cid)
                ms_call('ms_logout', [cid])
                yield alli_call('alli_logout', [cid])
                log.debug('User logout real. cid: {0}.'.format( cid ))
        else:
            log.error('User had logout. cid: {0}.'.format( cid ))

    @defer.inlineCallbacks
    def del_zombie_user(self, cid):
        ''' 清除僵尸玩家，无效client连接
        '''
        _user = self.user_dic.get(cid, None)
        if _user:
            if hasattr(_user, 'p'):
                if hasattr(_user.p, 'transport'):
                    if _user.p.transport:
                        defer.returnValue( NO_ERROR )
                    else:
                        log.error('Unknown user. cid:{0}, transport:{1}.'.format(cid, _user.p.transport))
                else:
                    log.warn('Unknown user. cid:{0}, the p has no transport attribute..'.format(cid))
            else:
                log.warn('__broadcast. cid:{0}, the user has no p attribute..'.format(_user.cid))

            self.delUserByCid( cid )
            gs_call('gs_logout', cid)
            ms_call('ms_logout', [cid])
            yield alli_call('alli_logout', [cid])
            log.warn('Del zombie user success. cid: {0}.'.format( cid ))
        defer.returnValue( NO_ERROR )

    def loseConnection(self, cid):
        user = self.user_dic.get(cid, None)
        if user:
            if hasattr(user, 'p') and user.p and user.p.transport:
                try:
                    user.p.transport.loseConnection()
                except Exception, e:
                    log.error('exception. cid: {0}, e: {1}.'.format( cid, e ))
            log.warn('Lose connection user success. cid: {0}.'.format( cid ))
        else:
            log.error('Unknown user. cid: {0}.'.format( cid ))
 
    @defer.inlineCallbacks
    def kickoutUser(self, cid):
        _user = self.user_dic.get(cid, None)
        if _user:
            self.delUserByCid( cid )
            yield gs_call('gs_kickout_user', [cid])
            ms_call('ms_logout', [cid])
            yield alli_call('alli_logout', [cid])

        defer.returnValue( NO_ERROR )

g_UserMgr = GateUserMgr()

