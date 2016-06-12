#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1


PORT = 8094

#数值DB配置
DB = {
        'host'         : '127.0.0.1',        #MySQL服务器TCP地址, 最好使用局域网地址，不要开放到外网
        'port'         : 3306,               #MySQL服务器TCP端口
        'user'         : 'root',             #MySQL账号
        'pass'         : 'db1234',           #账号的密码
        'db_sysconfig' : '3dk_sysconfig',    #系统数值database名称
        'pool_size'    : 50                  #持久连接池最大同时连接数
}

#游戏区Redis配置
REDIS = {
        #'redis_sock'   : '/tmp/redis.sock',  #Redis服务器Unix Socket地址。如果没有启用，请置空。
        'redis_host'   : '127.0.0.1',        #当redis_sock为空时，Redis服务器TCP地址, 最好使用局域网，不要开放到外网
        'redis_port'   : 6379,               #当redis_sock为空时，Redis服务器TCP端口
        'redis_db'     : 1,                  #本服使用的Redis服务器db序号
    }
