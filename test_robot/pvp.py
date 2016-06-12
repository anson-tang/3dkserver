#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import time
import sys, os
sys.path.insert(0, '../lib')

from twisted.python.log import startLogging, msg
from twisted.internet   import reactor, defer
from rpc                import ConnectorCreator

# log路径
log_path = r'./logs/pvp.log'
if os.path.exists(log_path):
    os.remove( log_path )
startLogging( open(log_path, 'w') )

# 服务器IP、port, 配置见../etc/env.conf
HOST = '192.168.8.233'
PORT = 28001

# 用于测试的用户数量
TOTAL_USER = 2
# 时间间隔
INTERVAL_ARENA = 5
INTERVAL_TREASURESHARD = 8

global RESULT
global DURATION
# 统计状态值
RESULT     = []
# 统计耗时
DURATION   = []

@defer.inlineCallbacks
def call_pvp(p, args):
    begin = time.time()
    res = [False, 0]
    if not p:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )

    # 登陆gateway
    error, char_data = yield p.call('login', args)
    if error:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )

    cid = char_data[0]['cid']
    # 获取所有的伙伴
    error, _ = yield p.call('fellow_list', [0])
    if error:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )
    # 获取玩家的阵容
    error, _ = yield p.call('get_player_camp', [cid])
    if error:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )
    # 获取玩家的布阵
    error, _ = yield p.call('get_fellow_formation', [])
    if error:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )
    # 已完成的剧情对话
    error, _ = yield p.call('finished_dialogue_group', [])
    if error:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )
    # 领奖中心奖励
    error, _ = yield p.call('award_center_info', [])
    if error:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )

    # pvp之竞技场
    call_arena(p)
    # pvp之夺宝
    yield call_treasureshard(p)

    res = True, time.time() - begin
    calDuration( res )
    defer.returnValue( res )

def calDuration(result):
    RESULT.append( result[0] )
    DURATION.append( result[1] )

    if len(RESULT) == TOTAL_USER or len(DURATION) == TOTAL_USER:
        #print 'RESULT:', RESULT, ', DURATION:', DURATION
        msg( 'Total: {0}, Success: {1}, Faild: {2}.'.format( len(RESULT), RESULT.count(True), RESULT.count(False) ) )
        msg( 'Max: {0}, Min: {1}, Avg: {2}.'.format( max(DURATION), min(DURATION), (sum(DURATION) / len(DURATION) if DURATION else 0) ) )
        #msg( '...... ...... ...... reactor stop ...... ...... ......\n' )

def call_arena(p):
    if p:
        p.call('get_arena_info', [])
        p.call('get_arena_ranklist', [])
        p.call('get_arena_lucky_ranklist', [])
 
    reactor.callLater(INTERVAL_ARENA, call_arena, p)

@defer.inlineCallbacks
def call_treasureshard(p):
    if p:
        yield p.call('get_plunder_info', [1])
        yield p.call('get_plunder_info', [2])
        p.call('avoid_player_list', [31001])
        p.call('avoid_player_list', [31002])
        p.call('avoid_player_list', [51001])
        p.call('avoid_player_list', [51002])

    reactor.callLater(INTERVAL_TREASURESHARD, call_treasureshard, p)

def errback(error):
    log.error('[ERROR] I have failed. ', error)

def connectServer():
    for _i in range(0, TOTAL_USER):
        conn = ConnectorCreator( call_pvp )
        d = conn.connect(HOST, PORT)
 
        account = u'test%s' % (_i+1)
        args = [u'1', account, u'sessionkey', u'1']
        d.addCallbacks( call_pvp, errback, (args, ) )




if __name__ == '__main__': 
    reactor.callWhenRunning( connectServer )
    msg( '\n...... ...... ...... reactor running ...... ...... ...... ' )
    reactor.run()


