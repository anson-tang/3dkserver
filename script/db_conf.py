#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import sys
import os


curr_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
print 'lib file path:', curr_path
sys.path.insert(0, curr_path)

from setting     import DB, REDIS

db_conf    = dict(host     = DB['host'],
                  port     = DB['port'],
                  user     = DB['user'],
                  passwd   = DB['pass'],
                  db       = DB['db_userdb'],
                  charset  = 'utf8',
                  )

print 'db_conf: ', db_conf


redis_sock = REDIS.get('redis_sock', None)
if redis_sock:
    redis_conf = dict(
            path = redis_sock, 
            dbid = REDIS['redis_db']
            )
else:
    redis_conf = dict(
            host = REDIS['redis_host'],
            port = REDIS['redis_port'],
            dbid = REDIS['redis_db']
            )

print 'redis_conf: ', redis_conf

