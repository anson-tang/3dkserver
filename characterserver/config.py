#!/usr/bin/env python
#-*-coding: utf-8-*-

from setting import DB, CHARACTERSERVER, syslog_address, log_threshold, log_path, log_rotate_interval, debug

interface    = None
port         = None
adminport    = None
db_conf      = None
syslog_conf  = None

def init(server_name):
    global interface, port, adminport, db_conf, syslog_conf

    interface  = CHARACTERSERVER['hostname']
    port       = CHARACTERSERVER['port']
    adminport  = CHARACTERSERVER['adminport']

    syslog_conf     = syslog_address

    db_conf    = dict(host     = DB['host'],
                      port     = DB['port'],
                      user     = DB['user'],
                      passwd   = DB['pass'],
                      db       = DB['db_userdb'],
                      charset  = 'utf8',
                      cp_noisy = debug,
                      cp_min   = 5,
                      cp_max   = DB['pool_size'],
                      cp_reconnect = True)
