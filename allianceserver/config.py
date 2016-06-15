#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from setting import REDIS, GATEWAYSERVER, MESSAGESERVER, ALLIANCESERVER, syslog_address, log_threshold, log_path, log_rotate_interval

gw_host     = None
gw_port     = None
ms_host     = None
ms_port     = None
alliance_id = None
interface   = None
port        = None
adminport   = None

syslog_conf       = None
redis_conf        = None

def init(server_name):
    global gw_host, gw_port, ms_host, ms_port, alliance_id, interface, port, adminport, redis_conf, syslog_conf

    gw_host     = GATEWAYSERVER['localhost']
    gw_port     = GATEWAYSERVER['port']
    ms_host     = MESSAGESERVER['hostname']
    ms_port     = MESSAGESERVER['port']
    alliance_id = ALLIANCESERVER['server_id']
    interface   = ALLIANCESERVER['hostname']
    port        = ALLIANCESERVER['port']
    adminport   = ALLIANCESERVER['adminport']

    syslog_conf = syslog_address
    redis_sock  = REDIS.get('redis_sock', None)

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

