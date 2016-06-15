#!/usr/bin/env python
#-*-coding: utf-8-*-

from setting import DB, REDIS, GATEWAYSERVER, syslog_address, log_threshold, log_path, log_rotate_interval, SERVER_ID

gateway_id  = None
port        = None
httport     = None
adminport   = None
syslog_conf = None
redis_conf  = None
server_id   = None

def init(server_name):
    global port, gateway_id, httport, redis_conf, adminport, syslog_conf, server_id

    server_id   = SERVER_ID
    gateway_id  = GATEWAYSERVER['server_id']
    port        = GATEWAYSERVER['port']
    httport     = GATEWAYSERVER['httport']
    adminport   = GATEWAYSERVER['adminport']

    redis_sock  = REDIS.get('redis_sock', None)
    syslog_conf = syslog_address

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

