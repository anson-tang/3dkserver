#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import random

from redis    import redis
from time     import time
from datetime import datetime
from log      import log
from marshal  import loads, dumps
from errorno  import *
from constant import *
from system   import sysconfig, get_robot_conf, get_treasureshard_rate_conf, get_item_by_itemid
from utils    import rand_num

from twisted.internet import reactor, defer
from models.activity  import load_offline_user_info


class AvoidWarMgr:
    '''
    redis key: 
            HASH_TREASURESHARD_ROBOT_RATE_shard_id-抢夺错失该碎片的累计概率
            TPL_TREASURE_SHARD_GOT_shard_id-拥有单个碎片的玩家信息
    '''
    Robots = []
    In_Plunders = {} # key:treasure_id, value:[plunder_cid, ...]

    @staticmethod
    def start_plunder_shard(treasure_id, plunder_cid):
        #log.info('For Test. start. treasure_id: {0}, plunder_cid: {1}, In_Plunders: {2}.'.format( treasure_id, plunder_cid, AvoidWarMgr.In_Plunders ))
        cids = AvoidWarMgr.In_Plunders.setdefault(treasure_id, [])
        if plunder_cid in cids:
            return IN_PLUNDER_ONGOING
        cids.append( plunder_cid )
        reactor.callLater(AVOID_USER_TIME_PLUNDER, AvoidWarMgr.stop_plunder_shard, treasure_id, plunder_cid)

        return NO_ERROR

    @staticmethod
    def stop_plunder_shard(treasure_id, plunder_cid):
        cids = AvoidWarMgr.In_Plunders.get(treasure_id, [])
        if plunder_cid in cids:
            cids.remove( plunder_cid )
        #log.info('For Test. stop. treasure_id: {0}, plunder_cid: {1}, In_Plunders: {2}.'.format( treasure_id, plunder_cid, AvoidWarMgr.In_Plunders ))

    @staticmethod
    def init_robot_data():
        for key in sysconfig.get('arena_robot').iterkeys():
            AvoidWarMgr.Robots.append(key)

    @staticmethod
    @defer.inlineCallbacks
    def remain_avoid_war_time(cid):
        _remain = 0

        _t = yield redis.hget( HASH_AVOID_WAR_TIME, cid )

        if _t:
            _remain = int(_t) - int(time())
            _remain = _remain if _remain > 0 else 0

        defer.returnValue( _remain )

    @staticmethod
    @defer.inlineCallbacks
    def inc_avoid_war_time(cid):
        _n = int(time())

        _t = yield redis.hget( HASH_AVOID_WAR_TIME, cid )
        _t = int(_t) if _t else _n
        if _n > _t:
            _t = _n

        _t += AVOID_WAR_SECONDS

        yield redis.hset( HASH_AVOID_WAR_TIME, cid, _t )

        defer.returnValue( _t - _n )

    @staticmethod
    @defer.inlineCallbacks
    def users_got_shards(shard_id, user_level, user_cid):
        '''
        @param: user_cid-玩家的cid
        @param: user_level-玩家的等级
        '''
        _users = []

        _hour = datetime.now().hour

        # 碎片对应的宝物配置
        treasure_id = 0
        item_conf   = get_item_by_itemid( shard_id )
        if item_conf:
            _, treasure_id, _ = item_conf['ChangeList'][0]
        plunder_cids = AvoidWarMgr.In_Plunders.get(treasure_id, [])

        robots_added = 0
        if _hour >= AVOID_USER_TIME_SPLIT and user_level > AVOID_WAR_LEVEL:
            _all = yield redis.hvals( TPL_TREASURE_SHARD_GOT % shard_id )
            _tmp_users = []

            for _iter in _all:
                _cid, _level, _name = loads( _iter )
                # 自己不能加入被抢夺列表
                if _cid == user_cid:
                    continue
                # 随机的玩家范围, 根据主角等级, 加减10级的范围内随机
                if abs(user_level - _level) <= 10:
                    # 免战后的玩家不会出现在任何人的夺宝列表中
                    _remain = yield AvoidWarMgr.remain_avoid_war_time( _cid )
                    if _remain > 0:
                        log.info('User in avoid war time. shard_id: {0}, treasure_id: {1}, cid: {2}.'.format( shard_id, treasure_id, _cid ))
                        continue
                    # 出现在其它人列表中的玩家过滤掉
                    if _cid in plunder_cids:
                        log.info('User in plundered. shard_id: {0}, treasure_id: {1}, cid: {2}.'.format( shard_id, treasure_id, _cid ))
                        continue
                    _tmp_users.append( [_cid, _level, _name, tuple()] )

            #从满足条件的玩家中随机出10个玩家的下标
            _len = len(_tmp_users)
            if _len > MAX_USERS_FOR_AVOID:
                _indexs = range(_len)
                random.shuffle( _indexs )

                for _idx in _indexs[:MAX_USERS_FOR_AVOID]: #随机后的前10个
                    major_level, _tmp_users[_idx][3], _ = yield load_offline_user_info(_tmp_users[_idx][0])
                    # 保存阵容失败的玩家
                    if _tmp_users[_idx][3]:
                        _tmp_users[_idx][1] = major_level if major_level else _tmp_users[_idx][1]
                        _users.append( _tmp_users[_idx] )
                    else:
                        log.warn('Error char camp data. data: {0}.'.format( _tmp_users[_idx] ))
                        yield redis.hdel( TPL_TREASURE_SHARD_GOT % shard_id, _tmp_users[_idx][0] )
            else:
                for _t in _tmp_users:
                    major_level, _t[3], _ = yield load_offline_user_info(_t[0])
                    # 保存阵容失败的玩家
                    if _t[3]:
                        _t[1] = major_level if major_level else _t[1]
                        _users.append( _t )
                    else:
                        log.warn('Error char camp data. data: {0}.'.format( _t ))
                        yield redis.hdel( TPL_TREASURE_SHARD_GOT % shard_id, _t[0] )

            robots_added = len(_users)

        log.info('Have user: {0}, user_ids: {1}.'.format( robots_added, [_u[0] for _u in _users] ))
        _len_robots  = len( AvoidWarMgr.Robots )
        _start_robot = 0
        if user_level <= 20:
            _start_robot = 3001
        elif user_level <= 30:
            _start_robot = 1001
        elif user_level <= 50:
            _start_robot = 101

        if _start_robot >= _len_robots:
            _start_robot = 0

        while 1:
            if not AvoidWarMgr.Robots or robots_added >= _len_robots: break
            if len( _users ) >= MAX_MEMBER_FOR_AVOID or robots_added >= MAX_MEMBER_FOR_AVOID: break

            robots_added += 1
            _key = AvoidWarMgr.Robots[ random.randint(_start_robot, _len_robots-1) ]
            _robot = get_robot_conf( _key )
            if _robot:
                _camp = map( int, _robot['RobotList'].split(',') )
                _users.append( ( 0, user_level, _robot['RobotName'], _camp ) )
            else:
                log.warn( "[ AvoidWarMgr.users_got_shards ]:No such robot in db. key:", _key, 'and type:', type(_key) )

        defer.returnValue( _users )

    @staticmethod
    @defer.inlineCallbacks
    def probability_of_robot(cid, shard_id, limit_rate):
        '''
        @summary: 获取玩家抢机器人时的概率
        @return : True-命中碎片 False-未命中
        '''
        _base_rate = 7500 # 机器人的基础概率

        _conf = get_treasureshard_rate_conf( shard_id )
        if _conf:
            _miss_rate = yield redis.hget( HASH_TREASURESHARD_ROBOT_RATE % shard_id, cid )
            if _miss_rate is None: # 新号第一次夺宝
                _miss_rate = _conf['MaxRate']
            else:
                _miss_rate = int(_miss_rate)

            _base_rate = _conf['Rate'] + _miss_rate
            if _base_rate >= _conf['MaxRate']:
                _base_rate = _conf['MaxRate']

            _miss_rate += _conf['AddRate']
        else:
            log.warn( 'No such conf in sysconfig:treasureshard_rate, shard_id:', shard_id )
            defer.returnValue( False )

        if limit_rate <= _base_rate: # 命中
            _miss_rate = 0
            yield redis.hset( HASH_TREASURESHARD_ROBOT_RATE % shard_id, cid, _miss_rate )
            defer.returnValue( True )
        else:
            yield redis.hset( HASH_TREASURESHARD_ROBOT_RATE % shard_id, cid, _miss_rate )
            defer.returnValue( False )

    @staticmethod
    @defer.inlineCallbacks
    def rand_shard(user, shard_id, plunder_cid):
        '''
        @summary: 获取碎片
        '''
        res_err = UNKNOWN_ERROR, None

        _rate   = rand_num()
        _flag   = False

        if plunder_cid > 0: # 玩家
            if _rate <= 7500:
                _flag = True
        else:
            _flag = yield AvoidWarMgr.probability_of_robot( user.cid, shard_id, _rate )

        if _flag:
            res_err = yield user.bag_treasureshard_mgr.new(shard_id, 1)

        defer.returnValue( res_err )

AvoidWarMgr.init_robot_data()
