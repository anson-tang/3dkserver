#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2014 Don.Li
# Summary: 

from twisted.internet.defer import inlineCallbacks, returnValue

from marshal  import loads, dumps
from time     import time

from log      import log
from redis    import redis
from constant import *

from protocol_manager  import gs_send, gw_send, ms_send
from syslogger         import syslogger


class Member( object ):
    def __init__( self, cid, name, lead_id, level, vip_level, might, rank, contribution, contribution_total, logoff_time, position, cd_time=0, dirty=False ):
        '''
        @param rank: 竞技场排名
        '''
        self.__cid         = cid
        self.__name        = name
        self.__lead_id     = lead_id
        self.__level       = level
        self.__vip_level   = vip_level
        self.__might       = might
        self.__rank        = rank
        self.__logoff_time = logoff_time
        self.__position    = position

        self.__contribution       = contribution
        self.__contribution_total = contribution_total

        self.cd_time = cd_time

        self.alliance = None
        self.__dirty  = dirty

    @property
    def cid( self ):
        return self.__cid
 
    @property
    def nick_name( self ):
        return self.__name
 
    @property
    def contribution( self ):
        return self.__contribution
 
    @property
    def contribution_total( self ):
        return self.__contribution_total
 
    @property
    def position( self ):
        return self.__position

    @property
    def might( self ):
        return self.__might

    @property
    def lead_id( self ):
        return self.__lead_id

    @property
    def name( self ):
        return self.__name

    @property
    def level( self ):
        return self.__level

    @property
    def vip_level( self ):
        return self.__vip_level

    @property
    def rank( self ):
        return self.__rank

    @property
    def isLeader(self):
        return self.__position == ALLIANCE_POSITION_LEADER
    
    @property
    def isViceLeader(self):
        return self.__position == ALLIANCE_POSITION_VICE
 
    @property
    def has_authority(self):
        return self.__position in [ALLIANCE_POSITION_LEADER, ALLIANCE_POSITION_VICE]

    def update_position(self, position, sync=True):
        '''
        @param: sync-True需要通知, False不需要通知
        '''
        if self.__position == position:
            return
        # 异常玩家
        if self.alliance and not self.__position:
            self.__position = ALLIANCE_POSITION_NORMAL
        # add syslog
        syslogger(LOG_ALLIANCE_POSITION, self.__cid, self.__level, self.__vip_level, self.alliance.aid, self.__position, position)

        self.__position = position
        self.__dirty = True
        ms_send('ms_alliance_position', (self.__cid, position))
        # 是否需要通知职位变化的在线玩家
        if sync and self.alliance:
            gw_send( self.__cid, 'sync_multicast', [SYNC_MULTICATE_TYPE_4, [self.alliance.aid, position]] )

    def rename(self, new_name):
        ''' 修改昵称 '''
        self.__name = new_name
        self.__dirty = True

    def update_lead_id(self, lead_id):
        ''' 升级主角 '''
        self.__lead_id = lead_id
        self.__dirty = True

    def update_level(self, level):
        ''' 等级提升 '''
        self.__level = level
        self.__dirty = True

    def update_vip_level(self, vip_level):
        ''' VIP等级提升 '''
        self.__vip_level = vip_level
        self.__dirty = True

    def update_might(self, might):
        ''' 战力改变 '''
        if self.__might == might:
            return
        ## 更新仙盟总战力
        #if self.alliance:
        #    delta_might = might - self.__might
        #    self.alliance.update_might( delta_might )

        # 更新个人战力
        self.__might = might if might > 0 else 0
        self.__dirty = True

    def update_arena_rank(self, arena_rank):
        ''' 更新竞技场排名 '''
        self.__rank = arena_rank
        self.__dirty = True

    def hall_get_contribution(self, count):
        ''' 建设大殿获取的个人贡献值 '''
        self.__contribution += count
        self.__contribution_total += count
        self.__dirty = True

    def delta_contribution(self, count):
        '''
        @param: count-增加或减少的个人贡献度
        '''
        self.__contribution += count
        if self.__contribution < 0:
            self.__contribution = 0
        self.__dirty = True

    @inlineCallbacks
    def login( self, name, level, vip_level, might, rank, lead_id ):
        self.__logoff_time = 0

        self.__name        = name
        self.__level       = level
        self.__vip_level   = vip_level
        self.__might       = might
        self.__rank        = rank
        self.__lead_id     = lead_id

        yield self.sync(force=True)

    @inlineCallbacks
    def logoff( self ):
        self.__logoff_time = int( time() )
        yield self.sync(force=True)

    @property
    def info(self):
        return [self.__cid, self.__name, self.__level, self.__lead_id, \
                self.__might, self.__rank, self.__contribution_total, \
                self.__contribution, self.__logoff_time, self.__position]

    @staticmethod
    def load( stream ):
        try:
            _cid, _name, _lead_id, _level, _vip_level, _might, _rank, _logoff_time, _position, \
                    _contribution, _contrib_total, _cd_time = loads( stream )
            _cd_time = _cd_time if _cd_time > int(time()) else 0
        except:
            log.exception()
            return None

        _m = Member( _cid, _name, _lead_id, _level, _vip_level, _might, _rank, _contribution,
                _contrib_total, _logoff_time, _position, _cd_time )

        return _m

    @inlineCallbacks
    def sync( self, force=False ):
        if self.__dirty or force:
            _info = self.__cid, self.__name, self.__lead_id, self.__level, self.__vip_level, \
                    self.__might, self.__rank, self.__logoff_time, self.__position, \
                    self.__contribution, self.__contribution_total, self.cd_time
            yield redis.hset( HASH_ALLIANCE_MEMBER, self.__cid, dumps( _info ) )
            self.__dirty = False

    def __str__( self ):
        _info = self.__cid, self.__name, self.__lead_id, self.__level, \
                self.__might, self.__rank, self.__logoff_time, self.__position

        return '<Member:i:{0},alliance:{1}>'.format( _info, self.alliance )
    __repr__ = __str__

    @inlineCallbacks
    def join_alliance(self, alliance, position=ALLIANCE_POSITION_NORMAL):
        if not self.alliance:
            self.alliance   = alliance
            # add syslog
            syslogger(LOG_ALLIANCE_POSITION, self.__cid, self.__level, self.__vip_level, self.alliance.aid, self.__position, position)

            self.__position = position
            yield self.sync(force=True)
            gs_send('gs_alliance_info', (self.__cid, (self.alliance.aid, self.alliance.name)))
            ms_send('ms_alliance_info', (self.__cid, (self.alliance.aid, self.alliance.name, self.__position)))
            gw_send( self.__cid, 'sync_multicast', [SYNC_MULTICATE_TYPE_7, []] )


    @inlineCallbacks
    def clean_alliance( self ):
        ''' 被踢出仙盟或其它 '''
        # add syslog
        _alliance_id = self.alliance.aid if self.alliance else 0
        syslogger(LOG_ALLIANCE_POSITION, self.__cid, self.__level, self.__vip_level, _alliance_id, self.__position, ALLIANCE_POSITION_NONE)

        self.alliance   = None
        self.__position = ALLIANCE_POSITION_NONE
        self.__contribution = self.__contribution_total = 0
        yield self.sync(force=True)
        gs_send('gs_alliance_info', (self.__cid, (0, '')))
        ms_send('ms_alliance_info', (self.__cid, (0, '', self.__position)))
        gw_send( self.__cid, 'sync_multicast', [SYNC_MULTICATE_TYPE_5, []] )

    @inlineCallbacks
    def leave_alliance( self ):
        ''' 主动离开仙盟 '''
        # add syslog
        _alliance_id = self.alliance.aid if self.alliance else 0
        syslogger(LOG_ALLIANCE_POSITION, self.__cid, self.__level, self.__vip_level, _alliance_id, self.__position, ALLIANCE_POSITION_NONE)

        self.alliance   = None
        self.__position = ALLIANCE_POSITION_NONE
        self.__contribution = self.__contribution_total = 0
        self.cd_time = int( time() ) + ALLIANCE_LEAVE_CD_TIME

        yield self.sync(force=True)
        gs_send('gs_alliance_info', (self.__cid, (0, '')))
        ms_send('ms_alliance_info', (self.__cid, (0, '', self.__position)))
        gw_send( self.__cid, 'sync_multicast', [SYNC_MULTICATE_TYPE_5, []] )


