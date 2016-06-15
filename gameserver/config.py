#!/usr/bin/env python
#-*-coding: utf-8-*-

from setting import DB, REDIS, \
        GATEWAYSERVER, GAMESERVER, MESSAGESERVER, ALLIANCESERVER, CHARACTERSERVER, \
        syslog_address, log_threshold, log_path, log_rotate_interval, debug

gw_host      = None
gw_port      = None
char_host    = None
char_port    = None
ms_host      = None
ms_port      = None
alli_host    = None
alli_port    = None
interface    = None
port         = None
adminport    = None
syslog_conf  = None
redis_conf   = None
user_db_conf = None
sysconfig_db_conf = None

def init(server_name):
    global interface, port, adminport, gw_host, gw_port, char_host, char_port, ms_host, ms_port, alli_host, alli_port, user_db_conf, sysconfig_db_conf, redis_conf, syslog_conf

    gw_host    = GATEWAYSERVER['localhost']
    gw_port    = GATEWAYSERVER['port']
    char_host  = CHARACTERSERVER['hostname']
    char_port  = CHARACTERSERVER['port']
    ms_host    = MESSAGESERVER['hostname']
    ms_port    = MESSAGESERVER['port']
    alli_host  = ALLIANCESERVER['hostname']
    alli_port  = ALLIANCESERVER['port']
    interface  = GAMESERVER['hostname']
    port       = GAMESERVER['port']
    adminport  = GAMESERVER['adminport']

    syslog_conf     = syslog_address

    user_db_conf    = dict(
                      host     = DB['host'],
                      port     = DB['port'],
                      user     = DB['user'],
                      passwd   = DB['pass'],
                      db       = DB['db_userdb'],
                      charaset = 'utf8',
                      cp_noisy = debug,
                      cp_min   = 5,
                      cp_max   = DB['pool_size'],
                      cp_reconnect = True)

    redis_sock = REDIS.get('redis_sock', None)

    if redis_sock:
        redis_conf = dict(
                path = redis_sock, 
                dbid = REDIS['redis_db'],
                password = REDIS['redis_passwd'],
                )
    else:
        redis_conf = dict(
                host = REDIS['redis_host'],
                port = REDIS['redis_port'],
                dbid = REDIS['redis_db'],
                password = REDIS['redis_passwd'],
                )

    sysconfig_db_conf = dict(
                 host    = DB['host'],
                 port    = DB['port'],
                 user    = DB['user'],
                 passwd  = DB['pass'],
                 db      = DB['db_sysconfig'],
                 charset = 'utf8',
             use_unicode = True)



