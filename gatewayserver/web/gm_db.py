#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 


from dbhelper         import DBHelper
from config           import DB


def db_config():

    _host = DB['host']
    _port = DB['port']
    _user = DB['user']
    _pass = DB['pass']
    _db   = DB['db_userdb']

    return {'host'       : _host, 
            'port'       : _port, 
            'user'       : _user, 
            'passwd'     : _pass, 
            'db'         : _db,
            'charset'    : 'utf8',
            'use_unicode': True
        }


try:
    db
except NameError:
    db = DBHelper(**db_config())

