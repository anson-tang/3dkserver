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
log_path = r'./logs/register.log'
if os.path.exists(log_path):
    os.remove( log_path )
startLogging( open(log_path, 'w') )

# 服务器IP、port, 配置见../etc/env.conf
HOST = '192.168.8.233'
PORT = 28001

# 用于测试的用户数量
TOTAL_USER = 2 

global RESULT
global DURATION
# 统计状态值
RESULT     = []
# 统计耗时
DURATION   = []

@defer.inlineCallbacks
def call_register(p, args):
    begin = time.time()
    res = [False, 0]
    if not p:
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )

    error, char_data = yield p.call('login', args)
    if not error:
        msg( '{0} had registed.'.format( args ) )
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )

    error, new_char_data = yield p.call('register', [1, args[1]])
    if error:
        msg('register error. new_res: {0}.'.format( (error, new_char_data) ))
        res[1] = time.time() - begin
        calDuration( res )
        defer.returnValue( res )
    #error, char_data = yield p.call('login', args)
    #if error:
    #    print ('login again error. res: {0}.'.format( (error, char_data) ))
    #    res[1] = time.time() - begin
    #    calDuration( res )
    #    defer.returnValue( res )

    res = True, time.time() - begin
    calDuration( res )
    defer.returnValue( res )

def calDuration(result):
    RESULT.append( result[0] )
    DURATION.append( result[1] )

    if len(RESULT) == TOTAL_USER or len(DURATION) == TOTAL_USER:
        #msg( 'RESULT: {0}, DURATION: {1}.'.format( RESULT, DURATION ) )
        msg( 'Total: {0}, Success: {1}, Faild: {2}.'.format( len(RESULT), RESULT.count(True), RESULT.count(False) ) )
        msg( 'Max: {0}, Min: {1}, Avg: {2}.'.format( max(DURATION), min(DURATION), (sum(DURATION) / len(DURATION) if DURATION else 0) ) )
        msg( '...... ...... ...... reactor stop ...... ...... ......\n' )
        reactor.stop()

def errback(error):
    log.error('[ERROR] I have failed. ', error)

def connectServer():
    for _i in range(0, TOTAL_USER):
        conn = ConnectorCreator( call_register )
        d = conn.connect(HOST, PORT)

        account = u'test%s' % (_i+1)
        args = [u'1', account, u'sessionkey', u'1']
        d.addCallbacks( call_register, errback, (args, ) )


if __name__ == '__main__': 
    reactor.callWhenRunning( connectServer )
    msg( '\n...... ...... ...... reactor running ...... ...... ...... ' )
    reactor.run()

