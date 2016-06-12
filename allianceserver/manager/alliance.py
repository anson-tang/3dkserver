#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2014 Don.Li
# Summary: 

import random
import Queue

from time                 import time
from twisted.internet     import reactor, defer
from marshal              import loads, dumps

from constant             import *
from errorno              import *
from log                  import log
from redis                import redis

from manager.member       import Member
from manager.request      import Request, del_request_to_dict
from manager.user         import g_UserMgr
from alli_system          import *
from protocol_manager     import ms_send, gs_call, gw_send, gw_broadcast, gs_send
from utils                import get_reset_timestamp, get_reward_timestamp, check_valid_time, timestamp_is_today
from syslogger            import syslogger


@defer.inlineCallbacks
def sync_dirty_alliance(queue, loop=True):
    _len = queue.qsize()
    if _len > 0:
        i = 0
        while i < _len:
            i += 1
            try:
                alliance = queue.get_nowait()
                yield alliance.sync()
            except Queue.Empty:
                break
            except Exception as e:
                log.error('sync alliance error. e: ', e)

    if loop:
        reactor.callLater(SYNC_ALLIANCE_INTERVAL, sync_dirty_alliance, queue)
    else:
        log.warn('End sync alliance. dirty alliance length: {0}.'.format( queue.qsize() ))


class Alliance( object ):
    def __init__( self, alliance_id, alliance_name, alliance_level, alliance_exp, description, notice='' ):
        self.__id       = alliance_id         #公会ID，内部唯一
        self.__name     = alliance_name       #公会名字，内部唯一
        self.__level    = alliance_level      #公会等级
        self.__exp      = alliance_exp        #公会经验

        self.__description = description      #公会宣言
        self.__notice   = notice              #公会公告

        self.__might    = 0                   #公会总战力
        #self.__rank     = 0                   #排行

        self.__leader_id    = 0                 #会长ID
        self.__leader_name  = ''                #会长昵称
        self.__leader_level = 0                 #会长等级
        self.__vice_leaders = []                #副会长列表

        self.__members    = []                #成员列表
        self.__requests   = {}                #申请加入公会的请求列表

        self.__building_levels = [1,1,1,1]    #公会建筑的等级列表
        # 脏数据的标志位 True-是脏数据, False-不是脏数据
        self.__dirty = False
        # 公会是否还存在的标志位 True-公会已解散, False-公会未解散
        self.deleted = False
        # 公会的动态信息 最多保存50条
        self.all_actions = []

    @property
    def aid( self ):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def level( self ):
        return self.__level

    @property
    def might( self ):
        return self.__might

    @property
    def leader_id(self):
        return self.__leader_id
    
    @property
    def building_levels(self):
        return  self.__building_levels
 
    @property
    def notice(self):
        ''' 仙盟公告 '''
        return self.__notice

    @property
    def members(self):
        return self.__members

    def revise_name(self, new_name):
        self.__name = new_name

    def revise_leader_name(self, new_name):
        self.__leader_name = new_name

    def online_cids(self, except_cids=[]):
        ''' 公会中在线成员的CID列表 
        @param: except_cids-需要排除的玩家CID列表
        '''
        _cids = []
        for _cid in self.__members:
            if _cid in except_cids:
                continue
            _m = g_UserMgr.getUser( _cid )
            if _m:
                _cids.append( _cid )
        return _cids

    def online_lead_cids(self, except_cids=[]):
        ''' 公会中在线的会长/副会长的CID列表 
        @param: except_cids-需要排除的玩家CID列表
        '''
        _cids = []
        for _cid in self.__vice_leaders:
            if _cid in except_cids:
                continue
            _m = g_UserMgr.getUser( _cid )
            if _m:
                _cids.append( _cid )

        if self.leader_id in except_cids:
            return _cids

        _m = g_UserMgr.getUser( self.leader_id )
        if _m:
            _cids.append( self.leader_id )

        return _cids

    def __str__( self ):
        return '<Alliance:{0},{1},{2}>'.format( self.__id, self.__name, self.__level )
    __repr__ = __str__

    def __eq__( self, other ):
        return isinstance( other, Alliance ) and self.__id == other.aid

    def __neq__( self, other ):
        return not isinstance( other, Alliance ) or self.__id != other.aid

    def __cmp__( self, other ):
        if not isinstance( other, Alliance ):
            return 1
        elif self.__level < other.level:
            return -1
        elif self.__level == other.level:
            if self.__might < other.might:
                return -1
            elif self.__might == other.might:
                return 0
            else:
                return 1
        else:
            return 1

    def dirty(self):
        if not self.__dirty:
            g_DirtyAllianceQueue.put(self)
            self.__dirty = True

    def appoint_leader(self, member, old_leader=None):
        self.__leader_id, self.__leader_name, self.__leader_level = member.cid, member.name, member.level
        # 通知在线玩家职位变化的标志位
        _notice_flag = False
        _m = g_UserMgr.getUser( member.cid )
        if _m:
            _notice_flag = True
        # 检查职位
        if member.cid in self.__vice_leaders:
            self.__vice_leaders.remove( member.cid )
        member.update_position( ALLIANCE_POSITION_LEADER, _notice_flag )

        # 公会动态
        if old_leader:
            self.new_action( (ALLIANCE_ACTION_4, int(time()), old_leader.cid, \
                    old_leader.lead_id, old_leader.nick_name, old_leader.level, [member.lead_id, member.nick_name]) )
        self.dirty()
        return NO_ERROR


    def appoint_vice(self, member, action_member):
        if len(self.__vice_leaders) >= ALLIANCE_VICE_MAX:
            return ALLIANCE_VICE_LIMIT_ERROR
        self.__vice_leaders.append( member.cid )
        # 通知在线玩家职位变化的标志位
        _notice_flag = False
        _m = g_UserMgr.getUser( member.cid )
        if _m:
            _notice_flag = True
        member.update_position( ALLIANCE_POSITION_VICE, _notice_flag )
        # 公会动态
        self.new_action( (ALLIANCE_ACTION_5, int(time()), action_member.cid, \
                action_member.lead_id, action_member.nick_name, action_member.level, [member.lead_id, member.nick_name]) )

        self.dirty()
        return NO_ERROR

    def appoint_normal(self, member, action_member):
        if member.cid in self.__vice_leaders:
            self.__vice_leaders.remove( member.cid )
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_10, int(time()), action_member.cid, \
                    action_member.lead_id, action_member.nick_name, action_member.level, [member.lead_id, member.nick_name]) )
        # 通知在线玩家职位变化的标志位
        _notice_flag = False
        _m = g_UserMgr.getUser( member.cid )
        if _m:
            _notice_flag = True
        member.update_position( ALLIANCE_POSITION_NORMAL, _notice_flag )
        return NO_ERROR

    @property
    def info( self ):
        return [ self.__id, self.__name, self.__level,
                self.__leader_id, self.__leader_name, self.__leader_level, 
                len( self.__members ), self.__might, self.__description, self.__exp ]

    @staticmethod
    @defer.inlineCallbacks
    def load( stream ):
        try:
            _alliance_id, _alliance_name, _alliance_level, _alliance_exp, _description, _mids, _notice = loads( stream )
            if not _mids:
                log.error( 'alliance<{0}, {1}> have no member.'.format( _alliance_id, _alliance_name ) )
                defer.returnValue( 0 )
        except:
            log.exception()
            defer.returnValue( 0 )

        _alliance = Alliance( _alliance_id,
                _alliance_name,
                _alliance_level,
                _alliance_exp,
                _description,
                _notice)

        _prepare_m = None
        _streams_member = yield redis.hmget( HASH_ALLIANCE_MEMBER, _mids )
        for _stream in _streams_member:
            if _stream:
                _m = Member.load( _stream )
                if _m:
                    _m.alliance = _alliance
                    _alliance.add_member( _m )
                    g_UserMgr.addUser( _m )
                    # 获取公会中的副会长 或者 等级最高的玩家
                    if not _prepare_m:
                        _prepare_m = _m
                    elif _m.isViceLeader or _m.level > _prepare_m.level:
                        _prepare_m = _m

        if _alliance.leader_id == 0:
            log.error( 'alliance<{0}, {1}> have no leader. _prepare_m: {2}.'.format( _alliance_id, _alliance_name, ((_prepare_m.cid, _prepare_m.name) if _prepare_m else None) ) )
            # 任命一个会长
            if _prepare_m:
                _prepare_m.update_position(ALLIANCE_POSITION_LEADER, False)
                _alliance.appoint_leader( _prepare_m )
        # 加载入会申请
        yield _alliance.load_requests_from_redis()
        # 加载建筑等级
        yield _alliance.load_building_level()

        defer.returnValue( _alliance )

    @property
    def stream( self ):
        return dumps( (self.__id,
                self.__name,
                self.__level,
                self.__exp,
                self.__description,
                self.__members, 
                self.__notice) )

    @defer.inlineCallbacks
    def sync( self ):
        if not self.__dirty or self.deleted:
            defer.returnValue( NO_ERROR )
 
        yield redis.hset( HASH_ALLIANCE_INFO, self.__id, self.stream )
        # 同步在线公会成员的信息, 离线玩家已经在下线时同步了
        for _cid in self.__members:
            _m = g_UserMgr.getUser( _cid )
            if _m:
                yield _m.sync()

    def add_member( self, member, dirty=False ):
        ''' 在服务器启动和公会创建时调用 更新公会战力和成员权限
        '''
        self.__members.append( member.cid )

        if member.isLeader:
            self.__leader_id    = member.cid
            self.__leader_name  = member.name
            self.__leader_level = member.level
        elif member.isViceLeader:
            self.__vice_leaders.append( member.cid )

        self.__might += member.might
        # 在公会创建时需要同步
        if dirty:
            self.dirty()

    def set_might(self, total_might):
        self.__might = total_might

    def update_might(self, delta_might):
        ''' 在有新成员加入公会时 更新公会的排行
        '''
        from server import server
        self.__might += delta_might
        self.__might = self.__might if self.__might > 0 else 0
        server.dirty_alliance( self )

    @defer.inlineCallbacks
    def del_member(self, member, action_member=None):
        ''' 在公会成员退出时不用实时更新公会战力 '''
        if member.cid in self.__members:
            self.__members.remove( member.cid )
            self.dirty()
        else:
            log.warn('delete member not in alliance member lists. cid: {0}, alliance_id: {1}.'.format( member.cid,  self.__id))
        if member.cid in self.__vice_leaders:
            self.__vice_leaders.remove( member.cid )
        if action_member:
            yield member.clean_alliance()
            ms_send('write_mail', (member.cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_6, [self.__name]))
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_3, int(time()), action_member.cid, \
                    action_member.lead_id, action_member.nick_name, action_member.level, [member.lead_id, member.nick_name]) )
        else:
            yield member.leave_alliance()
            ms_send('write_mail', (member.cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_5, [self.__name]))
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_2, int(time()), member.cid, member.lead_id, member.nick_name, member.level, []) )
        defer.returnValue( NO_ERROR )

    def del_invalid_member(self, member):
        ''' 处理公会中的异常玩家, 将他们踢出公会 '''
        if member.cid in self.__members:
            self.__members.remove( member.cid )
            self.dirty()
        if member.cid in self.__vice_leaders:
            self.__vice_leaders.remove( member.cid )

    @defer.inlineCallbacks
    def load_building_level(self):
        ''' 加载公会中的建筑物等级 '''
        _all_levels = yield redis.hget(HASH_ALLIANCE_LEVEL, self.__id)
        if _all_levels:
            self.__building_levels = loads(_all_levels)

    @defer.inlineCallbacks
    def load_requests_from_redis( self ):
        _all_requests = yield redis.lrange( TPL_LIST_ALLIANCE_REQUEST % self.__id, 0, -1 )
        for stream in _all_requests:
            _r = Request.load(stream, self)
            if _r:
                self.__requests[_r.cid] = _r

    def request_info(self):
        _times = []
        _infos = []
        for _r in self.__requests.itervalues():
            # 根据时间先后组织数据
            for _i, _time in enumerate(_times):
                if _r.request_time > _time:
                    _infos.insert(_i, _r.info)
                    break
            else:
                _infos.append( _r.info )
            _times.append( _r.request_time )

        return _infos

    @defer.inlineCallbacks
    def reject_all(self):
        # 对方没有公会时发送邮件
        for _cid, _r in self.__requests.iteritems():
            _m = yield g_UserMgr.get_offline_user( _cid )
            if _m and not _m.alliance:
                ms_send('write_mail', (_r.cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_4, [self.__name]))

        # 删除所有的入会申请
        yield self.del_all_requests()
        self.__requests = {}

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def del_all_requests(self):
        ''' 删除公会所有的入会申请 '''
        yield redis.delete( TPL_LIST_ALLIANCE_REQUEST % self.__id )
        del_request_to_dict( self.__requests.values() )

    def new_request(self, member):
        _r = self.__requests.get(member.cid, None)
        if _r:
            return NO_ERROR
        _r = Request.new(member.cid, member.name, member.lead_id, member.level, member.might, member.rank, self)
        self.__requests[member.cid] = _r
        return NO_ERROR

    @defer.inlineCallbacks
    def del_request(self, cid, join_flag=False, action_member=None):
        '''
        param  join_flag: True-同意加入公会 False-拒绝加入公会
        '''
        _r = self.__requests.get(cid, None)
        if not _r:
            defer.returnValue( ALLIANCE_REQUEST_UNKNOWN )

        _m = yield g_UserMgr.get_offline_user( cid )
        if not _m:
            log.warn('Unknown member. cid: {0}.'.format( cid ))
            defer.returnValue( NO_ERROR )

        # 对方没有公会且拒绝加入时发送邮件
        if not join_flag and not _m.alliance:
            ms_send('write_mail', (cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_4, [self.__name]))

        # 同意加入公会时检查公会成员人数限制之后再删除请求
        if join_flag:
            # 判断公会成员数量
            _conf = get_alliance_level_conf(self.__level)
            if not _conf:
                log.error('Can not find the conf. alliance_level: {0}.'.format( self.__level ))
                defer.returnValue( ALLIANCE_MEMBERS_MAX_ERROR )
            if len(self.__members) >= _conf['MembersCount']:
                defer.returnValue( ALLIANCE_MEMBERS_MAX_ERROR )

        del self.__requests[cid]
        yield redis.lrem( TPL_LIST_ALLIANCE_REQUEST % self.__id, 0, dumps(_r.info) )
        del_request_to_dict( [_r] )

        # 同意加入公会
        if join_flag:
            # 判断对方的公会状态
            if _m.alliance:
                defer.returnValue( ALLIANCE_OTHER_HAD_IN )
            yield _m.join_alliance( self )
            # 维护公会的公共信息
            self.__members.append( cid )
            self.dirty()
            self.update_might( _r.might )
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_1, int(time()), action_member.cid, \
                    action_member.lead_id, action_member.nick_name, action_member.level, [_m.lead_id, _m.nick_name]) )
            # 给对方发送邮件
            ms_send('write_mail', (cid, MAIL_PAGE_SYSTEM, MAIL_SYSTEM_3, [self.__name]))
        defer.returnValue( NO_ERROR )

    def update_description(self, desc_type, new_desc):
        ''' 更新公会宣言 '''
        if desc_type == ALLIANCE_DESC:
            self.__description = new_desc
        else:
            self.__notice = new_desc
        self.dirty()

        return NO_ERROR

    @defer.inlineCallbacks
    def upgrade_level(self, member, build_type):
        ''' 公会大殿升级, 大殿等级即公会等级 
        @param: build_type: 1-仙盟大殿, 2-仙盟女蜗宫, 3-仙盟商店, 4-仙盟副本, 5-仙盟任务大厅
        '''
        all_levels = get_all_alliance_level()
        if not all_levels:
            defer.returnValue( NOT_FOUND_CONF )
        max_level = max(all_levels)

        if build_type == 1:
            # 已是最高等级
            if self.__level >= max_level:
                defer.returnValue( ALLIANCE_LEVEL_MAX )
            # 公会建设度不足
            level_conf = get_alliance_level_conf( self.__level )
            if not level_conf:
                defer.returnValue( NOT_FOUND_CONF )
            need_contribution = level_conf['GuildHall']
            if self.__exp < need_contribution:
                defer.returnValue( ALLIANCE_CONTRIBUTE_NOT_ENOUGH )
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_9, int(time()), member.cid, member.lead_id, \
                    member.nick_name, member.level, [build_type, self.__level, self.__level+1]) )
            # 等级+1, 扣建设度
            self.__exp -= need_contribution
            self.__level += 1
            # 推送消息给公会当前在线的玩家, 除了自己
            _broadcast_cids = self.online_cids( [member.cid] )
            if _broadcast_cids:
                gw_broadcast( 'sync_multicast', [SYNC_MULTICATE_TYPE_6, [self.__id, self.__level, self.__exp]], _broadcast_cids )
            # add syslog
            syslogger(LOG_ALLIANCE_EXP_LOSE, member.cid, member.level, member.vip_level, \
                    self.__id, self.__level, need_contribution, self.__exp, WAY_ALLIANCE_HALL)
            # 脏数据
            self.dirty()
            defer.returnValue( (self.__level, self.__exp) )
        else:
            _fields = ['', '', 'GuildWelfareHall', 'GuildShop', 'GuildDungeon', 'GuildTask']
            if build_type >= len(_fields):
                defer.returnValue( REQUEST_LIMIT_ERROR )

            cur_level = self.__building_levels[build_type-2]
            # 已是最高等级
            if cur_level >= max_level:
                defer.returnValue( ALLIANCE_LEVEL_MAX )
            # 其它建筑等级不能超过公会等级
            if cur_level >= self.__level:
                defer.returnValue( ALLIANCE_LEVEL_LIMIT )
            # 公会建设度不足
            level_conf = get_alliance_level_conf( cur_level )
            if not level_conf:
                defer.returnValue( NOT_FOUND_CONF )
            need_contribution = level_conf[_fields[build_type]]
            if self.__exp < need_contribution:
                defer.returnValue( ALLIANCE_CONTRIBUTE_NOT_ENOUGH )
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_9, int(time()), member.cid, member.lead_id, \
                    member.nick_name, member.level, [build_type, cur_level, cur_level+1]) )
            # 等级+1, 扣建设度
            self.__exp -= need_contribution
            cur_level += 1
            self.__building_levels[build_type-2] = cur_level
            yield redis.hset(HASH_ALLIANCE_LEVEL, self.__id, dumps(self.__building_levels))
            # 推送消息给公会当前在线的玩家, 除了自己
            _broadcast_cids = self.online_cids( [member.cid] )
            if _broadcast_cids:
                gw_broadcast( 'sync_multicast', [SYNC_MULTICATE_TYPE_6, [self.__id, self.__level, self.__exp]], _broadcast_cids )
            # add syslog
            syslogger(LOG_ALLIANCE_EXP_LOSE, member.cid, member.level, member.vip_level, \
                    self.__id, self.__level, need_contribution, self.__exp, WAY_ALLIANCE_BUILD[build_type])
            # 脏数据
            self.dirty()
            defer.returnValue( (cur_level, self.__exp) )

    @defer.inlineCallbacks
    def hall_info(self, cid):
        ''' 公会成员的公会大殿的信息 '''
        _data = yield redis.hget(HASH_ALLIANCE_HALL, self.__id)
        if _data:
            _data = loads( _data )
            # 判断是否需要更新0点更新
            _reset_timestamp = get_reset_timestamp()
            if _data[0] <= _reset_timestamp:
                _data = [int(time()), [], []]
                yield redis.hset(HASH_ALLIANCE_HALL, self.__id, dumps(_data))
        else:
            _data = [int(time()), [], []]

        defer.returnValue( (_data[1], 0 if cid in _data[2] else 1, self.__level, self.__exp) )

    @defer.inlineCallbacks
    def hall_contribute(self, contribute_id, member):
        ''' 公会成员建设大殿 '''
        _data = yield redis.hget(HASH_ALLIANCE_HALL, self.__id)
        if _data:
            _data = loads( _data )
            # 判断是否需要更新0点更新
            _reset_timestamp = get_reset_timestamp()
            if _data[0] <= _reset_timestamp:
                _data = [int(time()), [], []]
        else:
            _data = [int(time()), [], []]
        # 当日已建设
        if member.cid in _data[2]:
            defer.returnValue( ALLIANCE_HAD_HALL_CONTRIBUTE )
        # 缺少配置
        _contribute_conf = get_alliance_contribution_conf(contribute_id)
        if not _contribute_conf:
            defer.returnValue( NOT_FOUND_CONF )
        # vip level限制
        if member.vip_level < _contribute_conf['VipLevel']:
            defer.returnValue( CHAR_VIP_LEVEL_LIMIT )
        # 所需道具是否充足
        if _contribute_conf['CostItemType'] != ITEM_TYPE_MONEY:
            defer.returnValue( UNKNOWN_ITEM_ERROR )
        # 扣道具
        errorno, left_golds, left_credits = yield gs_call('gs_alliance_hall_contribute', (member.cid, _contribute_conf['CostItemID'], _contribute_conf['CostItemNum']) )
        if errorno:
            defer.returnValue( errorno )
        # 更新基本信息
        _data[1].append( (member.nick_name, contribute_id) )
        _data[2].append( member.cid )
        yield redis.hset(HASH_ALLIANCE_HALL, self.__id, dumps(_data))
        # 给奖励 需要特殊处理
        _guild_num = 0
        for _type, _id, _guild_num in _contribute_conf['GuildAward']:
            if _type != ITEM_TYPE_MONEY or _id != ITEM_GUILD_CONTRIBUTE:
                log.error('Unknown award type. guild award conf: {0}.'.format( _contribute_conf['GuildAward'] ))
                continue
            self.__exp += _guild_num
        self.dirty()
        # 推送消息给公会当前在线的会长/副会长, 除了自己
        _broadcast_cids = self.online_lead_cids( [member.cid] )
        if _broadcast_cids:
            gw_broadcast( 'sync_multicast', [SYNC_MULTICATE_TYPE_6, [self.__id, self.__level, self.__exp]], _broadcast_cids )

        _persion_num = 0
        for _type, _id, _persion_num in _contribute_conf['PersonAward']:
            if _type != ITEM_TYPE_MONEY or _id != ITEM_MEMBER_CONTRIBUTE:
                log.error('Unknown award type. person award conf: {0}.'.format( _contribute_conf['PersonAward'] ))
                continue
            member.hall_get_contribution( _persion_num )
        # 公会动态
        if _guild_num > 0 or _persion_num > 0:
            if _contribute_conf['CostItemID'] == ITEM_MONEY_GOLDS:
                _action_type = ALLIANCE_ACTION_6
            else:
                _action_type = ALLIANCE_ACTION_7
            self.new_action( (_action_type, int(time()), member.cid, member.lead_id, member.nick_name, \
                    member.level, [_contribute_conf['CostItemNum'], _guild_num, _persion_num]) )

        #成就
        yield gs_send('gs_update_achievement', [member.cid, ACHIEVEMENT_QUEST_ID_24, self.level])
        # add syslog
        if _guild_num > 0:
            syslogger(LOG_ALLIANCE_EXP_GET, member.cid, member.level, member.vip_level, \
                    self.__id, _guild_num, self.__exp, WAY_ALLIANCE_HALL_CONTRIBUTE_IDS[contribute_id], '')
        if _persion_num > 0:
            syslogger(LOG_CONTRIBUTE_GET, member.cid, member.level, member.vip_level, self.__id, \
                    _persion_num, member.contribution, member.contribution_total, WAY_ALLIANCE_HALL_CONTRIBUTE_IDS[contribute_id], '')
        defer.returnValue( (self.__exp, member.contribution, member.contribution_total, left_golds, left_credits) )

    @defer.inlineCallbacks
    def sacrifice_info(self, member):
        ''' 公会女娲宫的信息 '''
        _data = yield redis.hget(HASH_ALLIANCE_SACRIFICE, self.__id)
        if _data:
            _data = loads( _data )
            # 判断是否需要更新0点更新
            _reset_timestamp = get_reset_timestamp()
            if _data[0] <= _reset_timestamp:
                _data = [int(time()), 0, []]
                yield redis.hset(HASH_ALLIANCE_SACRIFICE, self.__id, dumps(_data))
        else:
            _data = [int(time()), 0, []]
        # 获取玩家的拜祭信息
        for _cid, _contribution_count, _credits_count in _data[2]:
            if _cid == member.cid:
                break
        else:
            _contribution_count, _credits_count = 0, 0
 
        _a_level_conf = get_alliance_level_conf(self.__level)
        if not _a_level_conf:
            defer.returnValue( NOT_FOUND_CONF )
        _left_alliance_count = _a_level_conf['MembersCount'] - _data[1]
        _left_alliance_count = 0 if _left_alliance_count < 0 else _left_alliance_count

        _left_contribution_count = 0 if _contribution_count > 0 else 1
        _vip_level_conf = get_vip_conf(member.vip_level)
        if _vip_level_conf:
            _left_credits_count = _vip_level_conf['GuildSacrificeCount'] - _credits_count
            _left_credits_count = 0 if _left_credits_count < 0 else _left_credits_count
        else:
            _left_credits_count = 0

        defer.returnValue( (_left_alliance_count, _left_contribution_count, _left_credits_count, self.__level, self.__exp, _data) )

    @defer.inlineCallbacks
    def daily_sacrifice(self, sacrifice_type, member):
        ''' 公会成员拜祭女蜗宫
        '''
        _detail_count = yield self.sacrifice_info(member)
        if isinstance(_detail_count, int):
            defer.returnValue( _detail_count )
        _data = _detail_count[5]
        if sacrifice_type == ALLIANCE_SACRIFICE_NORMAL:
            # 次数不足
            if _detail_count[1] <= 0:
                defer.returnValue( SACRIFICE_NORMAL_COUNT_ERROR )
            if _detail_count[0] <= 0:
                defer.returnValue( SACRIFICE_ALLIANCE_COUNT_ERROR )
            # 个人可用贡献度不足
            if member.contribution < SACRIFICE_NEED_CONTRIBUTION:
                defer.returnValue( MEMBER_CONTRIBUTE_NOT_ENOUGH )
            # 给奖励
            _award_conf = get_sacrifice_award_conf( self.__building_levels[0] )
            if not _award_conf:
                defer.returnValue( NOT_FOUND_CONF )
            errorno, left_credits, add_items = yield gs_call('gs_alliance_sacrifice', (member.cid, 0, _award_conf))
            if errorno:
                defer.returnValue( errorno )
            # 扣个人贡献度
            member.delta_contribution( -SACRIFICE_NEED_CONTRIBUTION )
            # 扣拜祭次数
            _data[1] += 1
            for _idx, _value in enumerate(_data[2]):
                if _value[0] == member.cid:
                    _value[1] += 1
                    _data[2][_idx] = _value
                    break
            else:
                _data[2].append( [member.cid, 1, 0] )
            yield redis.hset(HASH_ALLIANCE_SACRIFICE, self.__id, dumps(_data))
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_8, int(time()), member.cid, member.lead_id, \
                    member.nick_name, member.level, [self.__building_levels[0]]) )
            # add syslog
            syslogger(LOG_CONTRIBUTE_LOSE, member.cid, member.level, member.vip_level, self.__id, \
                    SACRIFICE_NEED_CONTRIBUTION, member.contribution, member.contribution_total, WAY_ALLIANCE_SACRIFICE_NORMAL, '')

            defer.returnValue( (_detail_count[0]-1, _detail_count[1]-1, _detail_count[2], member.contribution, left_credits, add_items) )

        elif sacrifice_type == ALLIANCE_SACRIFICE_CREDITS:
            # 次数不足
            if _detail_count[2] <= 0:
                defer.returnValue( SACRIFICE_CREDITS_COUNT_ERROR )
            # 给奖励
            _award_conf = get_sacrifice_award_conf( self.__building_levels[0] )
            if not _award_conf:
                defer.returnValue( NOT_FOUND_CONF )
            errorno, left_credits, add_items = yield gs_call('gs_alliance_sacrifice', (member.cid, SACRIFICE_NEED_CREDITS, _award_conf))
            if errorno:
                defer.returnValue( errorno )
            # 扣拜祭次数
            for _idx, _value in enumerate(_data[2]):
                if _value[0] == member.cid:
                    _value[2] += 1
                    _data[2][_idx] = _value
                    break
            else:
                _data[2].append( [member.cid, 0, 1] )
            yield redis.hset(HASH_ALLIANCE_SACRIFICE, self.__id, dumps(_data))
            # 公会动态
            self.new_action( (ALLIANCE_ACTION_8, int(time()), member.cid, member.lead_id, \
                    member.nick_name, member.level, [self.__building_levels[0]]) )
            # add syslog
            syslogger(LOG_CONTRIBUTE_LOSE, member.cid, member.level, member.vip_level, self.__id, \
                    0, member.contribution, member.contribution_total, WAY_ALLIANCE_SACRIFICE_CREDITS, '')

            defer.returnValue( (_detail_count[0], _detail_count[1], _detail_count[2]-1, member.contribution, left_credits, add_items) )

        else:
            defer.returnValue( REQUEST_LIMIT_ERROR )

    @defer.inlineCallbacks
    def random_limit_item(self, level):
        ''' 随机每天的3个珍宝道具
        '''
        limit_conf = get_shop_limit_conf(level)
        if not limit_conf:
            defer.returnValue( [] )

        random_data = yield redis.hget( HASH_ALLIANCE_LIMIT_ITEM_RANDOM, self.__id )
        if random_data:
            last_level, random_data = loads(random_data)
            if last_level != level:
                random_data = {}
        else:
            random_data = {}

        items_pool = [] # 珍宝随机池
        items_ids  = [] # 随机到的item_id
        for _s_id, _item in limit_conf.iteritems():
            _rate = (_item['Rate'] + _item['AddRate'] * random_data.get(_s_id, 0))
            _rate = _rate if _rate < _item['MaxRate'] else _item['MaxRate']
            items_pool.extend( [_s_id]*_rate )

        if items_pool:
            for i in range(0, 3):
                items_ids.append( random.choice(items_pool) )
        else:
            log.error('Alliance limit item random pool is null.')
        # 累计次数提高比例
        for _s_id, _item in limit_conf.iteritems():
            # 已抽中的道具累计次数清零
            if _s_id in items_ids:
                if random_data.has_key( _s_id ):
                    del random_data[_s_id]
                continue
            if (not _item['AddRate']):
                continue
            # 剩下未抽中的道具累计次数加1
            random_data[_s_id] = random_data.setdefault(_s_id, 0) + 1
        yield redis.hset( HASH_ALLIANCE_LIMIT_ITEM_RANDOM, self.__id, dumps([level, random_data]) )

        if not items_ids:
            log.error('No random limit items. alliance_level: {0}, items_ids: {1}.'.format( level, items_ids ))
        defer.returnValue( items_ids )

    @defer.inlineCallbacks
    def limit_item_info(self, member):
        ''' 仙盟商店中珍宝的兑换信息 '''
        _data = yield redis.hget(HASH_ALLIANCE_LIMIT_ITEM, self.__id)
        if _data:
            _data = loads( _data )
            # 判断是否是12点需要更新
            _reset_timestamp = get_reset_timestamp(12)
            if _data[0] <= _reset_timestamp:
                random_item_ids = yield self.random_limit_item( self.__level )
                if not random_item_ids:
                    log.error('Not found limit item conf. alliance_id: {0}, level: {1}.'.format( self.__id, self.__level ))
                    defer.returnValue( NOT_FOUND_CONF )
                _data = [int(time()), self.__level, [[_s_id, []] for _s_id in random_item_ids]]
                yield redis.hset(HASH_ALLIANCE_LIMIT_ITEM, self.__id, dumps(_data))
        else:
            random_item_ids = yield self.random_limit_item( self.__level )
            if not random_item_ids:
                log.error('Not found limit item conf. alliance_id: {0}, level: {1}.'.format( self.__id, self.__level ))
                defer.returnValue( NOT_FOUND_CONF )
            _data = [int(time()), self.__level, [[_s_id, []] for _s_id in random_item_ids]]
            yield redis.hset(HASH_ALLIANCE_LIMIT_ITEM, self.__id, dumps(_data))

        limit_items = [] # 珍宝的详细信息
        limit_conf  = get_shop_limit_conf( _data[1] )
        for _idx, _detail in enumerate(_data[2]):
            _item = limit_conf.get( _detail[0], None )
            if _item:
                _left_count = _item['BuyMax'] - len(_detail[1])
                _left_count = 0 if _left_count < 0 else _left_count
                # 是否已兑换的标志位
                _status = 0 if member.cid in _detail[1] else 1
                limit_items.append( (_idx, _item['ItemType'], _item['ItemID'], _item['ItemNum'], _left_count, _item['Cost'], _status) )
        # 距离下一次刷新还需要的秒数
        need_seconds = get_reward_timestamp(hours=12) - int(time())

        defer.returnValue( (need_seconds, limit_items, self.__level, self.__exp) )

    @defer.inlineCallbacks
    def limit_item_exchange(self, member, index):
        ''' 仙盟商店中兑换珍宝 '''
        _data = yield redis.hget(HASH_ALLIANCE_LIMIT_ITEM, self.__id)
        if not _data:
            defer.returnValue( REFRESH_ITEM_ERROR )

        _data = loads( _data )
        # 判断是否是12点需要更新
        _reset_timestamp = get_reset_timestamp(12)
        if _data[0] <= _reset_timestamp or len(_data[2]) <= index:
            defer.returnValue( REFRESH_ITEM_ERROR )
 
        detail = _data[2][index]

        limit_conf  = get_shop_limit_conf( _data[1] )
        item_conf = limit_conf.get( detail[0], None )
        if not item_conf:
            defer.returnValue( NOT_FOUND_CONF )
        # 检查是否重复兑换
        if member.cid in detail[1]:
            defer.returnValue( EXCHANGE_ITEM_REPEAT_ERROR )
        # 检查可兑换次数
        _left_count = item_conf['BuyMax'] - len(detail[1])
        if _left_count <= 0:
            defer.returnValue( EXCHANGE_ITEM_COUNT_NOT_ENOUGH )
        # 检查个人贡献是否满足
        if member.contribution < item_conf['Cost']:
            defer.returnValue( MEMBER_CONTRIBUTE_NOT_ENOUGH )
        # 兑换道具
        items_list = [[item_conf['ItemType'], item_conf['ItemID'], item_conf['ItemNum']]]
        errorno, add_items = yield gs_call('gs_exchange_item', (member.cid, WAY_ALLIANCE_LIMIT_ITEM, items_list))
        if errorno:
            defer.returnValue( errorno )
        # 更新兑换记录
        detail[1].append( member.cid )
        _data[2][index] = detail
        yield redis.hset(HASH_ALLIANCE_LIMIT_ITEM, self.__id, dumps(_data))
        # 扣个人贡献度
        member.delta_contribution( -item_conf['Cost'] )
        # add syslog
        syslogger(LOG_CONTRIBUTE_LOSE, member.cid, member.level, member.vip_level, self.__id, \
                item_conf['Cost'], member.contribution, member.contribution_total, WAY_ALLIANCE_LIMIT_ITEM, '(%s,)'%(detail[0]))

        defer.returnValue( (index, _left_count-1, member.contribution, add_items) )

    @defer.inlineCallbacks
    def item_info(self, member):
        ''' 仙盟商店-道具的兑换信息 '''
        _data = yield redis.hget(HASH_ALLIANCE_ITEM, member.cid)
        if _data:
            _data = loads( _data )
            # 判断是否是12点需要更新
            _reset_timestamp = get_reset_timestamp(12)
            if _data[0] <= _reset_timestamp:
                _data = [int(time()), [], self.__level, self.__exp]
                yield redis.hset(HASH_ALLIANCE_ITEM, member.cid, dumps(_data))
        else:
            _data = [int(time()), [], self.__level, self.__exp]

        defer.returnValue( _data )

    @defer.inlineCallbacks
    def item_exchange(self, member, shop_item_id): 
        ''' 仙盟商店-兑换道具 '''
        item_conf = get_shop_item_conf( shop_item_id )
        if not item_conf:
            defer.returnValue( NOT_FOUND_CONF )
        # 道具的公会等级限制
        if self.__level < item_conf['GuildLevel']:
            defer.returnValue( ALLIANCE_LEVEL_LIMIT )
        # 检查个人贡献是否满足
        if member.contribution < item_conf['Cost']:
            defer.returnValue( MEMBER_CONTRIBUTE_NOT_ENOUGH )
        # 检查今日兑换次数是否充足
        exchange_count = 0
        exchange_info  = yield self.item_info(member)
        for _idx, _detail in enumerate(exchange_info[1]):
            if _detail[0] == shop_item_id:
                if _detail[1] >= item_conf['BuyMax']:
                    defer.returnValue( EXCHANGE_ITEM_COUNT_NOT_ENOUGH )
                _detail[1] += 1
                exchange_count = _detail[1]
                exchange_info[1][_idx] = _detail
                break
        else:
            exchange_count = 1
            exchange_info[1].append( [shop_item_id, 1] )
        # 兑换道具
        items_list = [[item_conf['ItemType'], item_conf['ItemID'], item_conf['ItemNum']]]
        errorno, add_items = yield gs_call('gs_exchange_item', (member.cid, WAY_ALLIANCE_ITEM, items_list))
        if errorno:
            defer.returnValue( errorno )
        # 更新兑换记录
        yield redis.hset(HASH_ALLIANCE_ITEM, member.cid, dumps(exchange_info))
        # 扣个人贡献度
        member.delta_contribution( -item_conf['Cost'] )
        # add syslog
        syslogger(LOG_CONTRIBUTE_LOSE, member.cid, member.level, member.vip_level, self.__id, \
                item_conf['Cost'], member.contribution, member.contribution_total, WAY_ALLIANCE_ITEM, '(%s,)'%(shop_item_id))

        defer.returnValue( (shop_item_id, exchange_count, member.contribution, add_items) )

    def new_action(self, action):
        self.all_actions.append( action )
        if len(self.all_actions) > ACTION_COUNT_LIMIT:
            self.all_actions = self.all_actions[-ACTION_COUNT_LIMIT:]

    def get_all_actions(self, index):
        ''' 返回仙盟的动态 '''
        _total = len(self.all_actions)
        if index > 0:
            _actions = self.all_actions[-index-ACTION_PER_PAGE:-index]
        else:
            _actions = self.all_actions[-ACTION_PER_PAGE:]
        _actions.reverse()
        return (index, _total, _actions)

    @defer.inlineCallbacks
    def get_all_messages(self, member, index):
        ''' 获取当前留言 '''
        _had_count, _, _details = yield self.check_valid_messages(member.cid, flag=True)
        _left_count = MESSAGES_DAILY_MAX - _had_count
        if _left_count < 0:
            _left_count = 0

        _details = _details[-MESSAGES_COUNT_LIMIT:]
        defer.returnValue( (index, len(_details), _left_count, _details) )

    @defer.inlineCallbacks
    def new_messages(self, member, content):
        ''' 新增留言 '''
        _had_count, _all_messages, _ = yield self.check_valid_messages(member.cid)
        if _had_count >= MESSAGES_DAILY_MAX:
            defer.returnValue( ALLIANCE_MESSAGES_MAX_ERROR )

        _all_messages.append( (int(time()), member.cid, content) )
        _all_messages = _all_messages[-MESSAGES_COUNT_LIMIT:]
        yield redis.hset(HASH_ALLIANCE_MESSAGES, self.__id, dumps(_all_messages))

        defer.returnValue( NO_ERROR )

    @defer.inlineCallbacks
    def check_valid_messages(self, cid, flag=False):
        ''' 
        @param: flag-True:需要详细信息的标志位, False:不需要详情
        '''
        _all_messages = yield redis.hget(HASH_ALLIANCE_MESSAGES, self.__id)
        if _all_messages:
            _all_messages = loads(_all_messages)
        else:
            _all_messages = []

        _daily_count    = 0 # 今日已留言的次数
        _valid_messages = []
        _details = []
        for _message in _all_messages:
            _m = g_UserMgr.getUser( _message[1] )
            if not _m:
                continue
            # 检查时间是否过期, 7天
            if check_valid_time(_message[0], hour=MESSAGES_VALID_HOUR):
                continue
            if cid == _m.cid and timestamp_is_today(_message[0]):
                _daily_count += 1
            _valid_messages.append( _message )
            if flag:
                _details.append( (_message[0], _m.cid, _m.lead_id, _m.nick_name, _m.level, _m.position, _message[2]) )

        defer.returnValue( (_daily_count, _valid_messages, _details) )


try:
    g_DirtyAllianceQueue
except NameError:
    g_DirtyAllianceQueue = Queue.Queue()
    reactor.callLater(SYNC_ALLIANCE_INTERVAL, sync_dirty_alliance, g_DirtyAllianceQueue)
    reactor.addSystemEventTrigger('before', 'shutdown', sync_dirty_alliance, g_DirtyAllianceQueue, False)

