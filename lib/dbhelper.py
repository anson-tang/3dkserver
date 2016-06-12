#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summaron: 0.1.0

from twisted.enterprise import adbapi
from twisted.internet import defer
from log import log
import MySQLdb
import traceback
import sys

class ReconnectingConnectionPool(adbapi.ConnectionPool):
    def _runInteraction(self, interaction, *args, **kw):
        conn = self.connectionFactory(self)
        trans = self.transactionFactory(self, conn)

        try:
            result = interaction(trans, *args, **kw)
            trans.close()
            conn.commit()
            return result
        except MySQLdb.OperationalError, e:
            if e[0] in (2006, 2013):
                log.info("RCP: got error %s, retrying operation" %(e))
                conn = self.connections.get(self.threadID())
                self.disconnect(conn)
                return self._runInteraction(interaction, *args, **kw)
            else:
                #traceback.print_exc()
                excType, excValue, excTraceback = sys.exc_info()
                try:
                    conn.rollback()
                except Exception, e:
                    log.exception("Roll failed.")

                raise excType, excValue, excTraceback
        except:
            #traceback.print_exc()
            excType, excValue, excTraceback = sys.exc_info()
            raise excType, excValue, excTraceback

class DBHelper(object):
    def __init__(self, **config):
        self.dbpool = ReconnectingConnectionPool('MySQLdb', **config)
    
    def getPool(self):
        return self.dbpool
    
    def query(self, sql):
        return self.dbpool.runQuery(sql)#.addCallbacks(callback, self.error, callbackArgs=args)
    
    def execute(self, sql, *args):
        return self.dbpool.runOperation(sql, *args)#.addErrback(self.error)
    
    def insert(self, sql, value):
        return self.dbpool.runInteraction(self.__insertAndReturnInsertId, sql, value)#.addErrback(self.error)
    
    def __insertAndReturnInsertId(self, txn, sql, value):
        txn.execute(sql, value)
        return txn._connection.insert_id()
        
    def executemany(self, sql, values):
        return self.dbpool.runInteraction(self.__execmany, sql, values)#.addErrback(self.error)
    
    def __execmany(self, txn, sql, values):
        return txn.executemany(sql, values)
    
    def __querymany(self, txn, sqls):
        result = []
        
        idx = len(sqls)
        sql = ';'.join(sqls)

        txn.execute(sql)
        
        while idx > 0:
            result.append(txn.fetchall())        
            txn.nextset()
            idx -= 1
            
        return result
    
    def queryMany(self, sqls=[]):
        return self.dbpool.runInteraction(self.__querymany, sqls)#.addErrback(self.error)
