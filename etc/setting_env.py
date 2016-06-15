#-*-coding: utf-8-*-

#关闭后，一些debug功能会被关闭，不影响log等级
#debug = True                                 

#接入第三方平台时，切换沙盒状态
#sandbox = True                               

#可设置为: 'debug', 'info', 'warn', 'error', 'crit'
#log_threshold = 'debug'                      

#服务器运行日志的绝对路径
log_path = '/root/workspace/3dkserver/logs/' 

#日志文件多大时会被rotate
#log_rotate_interval = 104857600              

#最多接受客户端TCP连接数
#max_clients_per_svc = 5000                   

#多少秒后,服务器会停止进程
#seconds_for_stop = 0                         

#用于记录玩家行为日志的SYSLog服务器TCP地址
#syslog_address = '127.0.0.1,10515'          


#游戏区DB配置
DB = {
        'host'         : '127.0.0.1',        #MySQL服务器TCP地址, 最好使用局域网地址，不要开放到外网
        'port'         : 13306,               #MySQL服务器TCP端口
        'user'         : '3dk-server',             #MySQL账号
        'pass'         : '3dk-0#Ser.ver',           #账号的密码
        'db_sysconfig' : '3dk_sysconfigdb',  #系统数值database名称
        'db_userdb'    : '3dk_userdb',     #玩家数据database名称
        'pool_size'    : 50                  #持久连接池最大同时连接数
    }

#游戏区Redis配置
REDIS = {
        'redis_sock'   : '/tmp/redis.sock',  #Redis服务器Unix Socket地址。如果没有启用，请置空。
        'redis_host'   : '127.0.0.1',        #当redis_sock为空时，Redis服务器TCP地址, 最好使用局域网，不要开放到外网
        'redis_port'   : 10379,               #当redis_sock为空时，Redis服务器TCP端口
        'redis_db'     : 6,                   #本服使用的Redis服务器db序号
        'redis_passwd' : 'Redis.Passwd',
    }

#游戏区服务器起始TCP端口
PORT      = 11000

#游戏区编号
SERVER_ID = 101

#游戏区网关对外域名或IP地址
HOST_GW   = '120.26.229.89'

#游戏区网关内部IP地址
HOST_GW_LOCAL  = '127.0.0.1'

#游戏区游戏服务器内部IP地址
HOST_GAME      = '127.0.0.1'

#游戏区游戏服务器内部IP地址
HOST_MESSAGE   = '127.0.0.1'

#游戏区游戏服务器内部IP地址
HOST_CHARACTER = '127.0.0.1'
