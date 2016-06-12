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
from twisted.internet import reactor, defer
from rpc              import ConnectorCreator

# log路径
log_path = r'./logs/broadcast.log'
if os.path.exists(log_path):
    os.remove( log_path )
startLogging( open(log_path, 'w') )

# 服务器IP、port, 配置见../etc/env.conf
HOST = '192.168.8.233'
PORT = 28001

# 用于测试的用户数量
TOTAL_USER = 2
# 广播的间隔时间
INTERVAL   = 5
# 统计状态值
RESULT     = []

@defer.inlineCallbacks
def call_broadcast(p, args):
    begin = time.time()
    res = [False, 0]
    if not p:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )

    # 登陆gateway
    account = args[1]
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
    
    # 对全服在线的玩家广播
    call_broadcast(p)

    res = True, time.time() - begin
    calDuration( res )
    defer.returnValue( res )


def call_broadcast(p):
    if p:
        # 全服广播
        p.call('broadcast', ['sync_broadcast', [[3, [2, ['test***', 3, [23091, 23092, 23093, 23094, 23095, 23096, 23097]]]]]])

    reactor.callLater(INTERVAL, call_broadcast, p)

def calDuration(result):
    RESULT.append( result[0] )

    if len(RESULT) == TOTAL_USER:
        msg( 'Total: {0}, Success: {1}, Faild: {2}.'.format( len(RESULT), RESULT.count(True), RESULT.count(False) ) )


def errback(error):
    log.error('[ERROR] I have failed. ', error)

def connectServer():
    for _i in range(0, TOTAL_USER):
        conn = ConnectorCreator( call_broadcast )
        d = conn.connect(HOST, PORT)
 
        account = u'test%s' % (_i+1)
        args = [u'1', account, u'sessionkey', u'1']
        d.addCallbacks( call_broadcast, errback, (args, ) )


if __name__ == '__main__': 
    reactor.callWhenRunning( connectServer )
    msg( '\n...... ...... ...... reactor running ...... ...... ...... ' )
    reactor.run()



