#!/usr/bin/env python
#-*-coding: utf-8-*-

from twisted.internet.protocol import ServerFactory
from twisted.internet          import defer
from twisted.internet          import reactor

from rpc              import GeminiRPCProtocol, load_all_handlers
from os.path          import abspath, dirname
from protocol_manager import protocol_manager
from manager.gateuser import g_UserMgr

import MySQLdb
import time

from config   import DB
from redis    import redis
from constant import DICT_ACCOUNT_REGISTERED, DICT_NICKNAME_REGISTERED, SET_CID_REGISTERED
from log     import log

class Server(ServerFactory):
    protocol = GeminiRPCProtocol

    def startFactory(self):
        print '=============================\n'
        print '*   GateWay Server Start!   *\n'
        print '============================='
        load_all_handlers(dirname(abspath(__file__)) + '/', 'handler')

        self.__migrate_accounts_registered()

    @defer.inlineCallbacks
    def __migrate_accounts_registered(self):
        try:
            yield redis.delete( DICT_ACCOUNT_REGISTERED )
            yield redis.delete( DICT_NICKNAME_REGISTERED )
            yield redis.delete( SET_CID_REGISTERED )

            db_conf = {'host': DB['host'],
                'port'       : DB['port'],
                'user'       : DB['user'],
                'passwd'     : DB['pass'],
                'db'         : DB['db_userdb'],
                'charset'    : 'utf8'
                }

            conn = MySQLdb.connect(**db_conf)
            cu   = conn.cursor()

            cu.execute('SELECT `account`,`nick_name`,`id`,`sid` FROM tb_character')
            _dataset = cu.fetchall()
            for _account_name, _nick_name, _id, _sid in _dataset:
                yield redis.hset(DICT_ACCOUNT_REGISTERED, '%s%s'%(_account_name,_sid), _id)
                yield redis.hset(DICT_NICKNAME_REGISTERED, _nick_name, _id)
                yield redis.sadd(SET_CID_REGISTERED, _id)

            cu.close()
            conn.close()

            conn = None
            cu   = None
        except Exception, e:
            reactor.callLater(1, self.__migrate_accounts_registered)
            print 'ERROR:', e
            print 'WARNING. Redis connection fail, callLater 1 second. redis:', redis

    def stopFactory(self):
        print '=============================\n'
        print '*  GateWay Server Stop!     *\n'
        print '============================='

    def cleanup(self):
        pass

    def onConnectionMade(self, p):
        pass

    def onConnectionLost(self, p):
        if hasattr(p, 'cid') and p.cid:
            log.warn('cid<{0}> lose connection.'.format( p.cid ))
            g_UserMgr.logoutUser(p.cid)

