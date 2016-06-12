#-*-coding: utf-8-*-

#关闭后，一些debug功能会被关闭，不影响log等级
debug = True                                 

#接入第三方平台时，切换沙盒状态
sandbox = True                               

#可设置为: 'debug', 'info', 'warn', 'error', 'crit'
log_threshold = 'debug'                      

#服务器运行日志的绝对路径
log_path = '/home/likai/3d3k/Program/trunk/Server/logs/' 

#日志文件多大时会被rotate
log_rotate_interval = 104857600              

#最多接受客户端TCP连接数
max_clients_per_svc = 5000                   

#服务器停止是否需要倒计时和使用switcher命令来切换开关
need_switch = False

#用于记录玩家行为日志的SYSLog服务器TCP地址
syslog_address = '127.0.0.1,10515'          


#游戏区DB配置
DB = {
        'host'         : '127.0.0.1',        #MySQL服务器TCP地址, 最好使用局域网地址，不要开放到外网
        'port'         : 3306,               #MySQL服务器TCP端口
        'user'         : 'root',             #MySQL账号
        'pass'         : 'db1234',           #账号的密码
        'db_sysconfig' : 'tc3dk_sysconfig',  #系统数值database名称
        'db_userdb'    : 'nh_3d3k_char',     #玩家数据database名称
        'pool_size'    : 50                  #持久连接池最大同时连接数
    }

#游戏区Redis配置
REDIS = {
        'redis_sock'   : '/tmp/redis.sock',  #Redis服务器Unix Socket地址。如果没有启用，请置空。
        'redis_host'   : '127.0.0.1',        #当redis_sock为空时，Redis服务器TCP地址, 最好使用局域网，不要开放到外网
        'redis_port'   : 6379,               #当redis_sock为空时，Redis服务器TCP端口
        'redis_db'     : 2                   #本服使用的Redis服务器db序号
    }

PORT      = 11000
SERVER_ID = 101
HOST_GW   = '192.168.8.233'
HOST_GW_LOCAL = HOST_GAME = HOST_MESSAGE = HOST_CHARACTER = HOST_ALLIANCE = '127.0.0.1'
execfile(__file__.rsplit('/', 1)[0] + '/../etc/setting_env.py')

#游戏区网关配置
GATEWAYSERVER = {
        'server_id' : SERVER_ID,          #网关服务器编号
        'hostname'  : HOST_GW,            #网关开放给客户端的域名或IP地址
        'localhost' : HOST_GW_LOCAL,      #网关局域网内IP地址
        'port'      : PORT,               #网关TCP端口
        'httport'   : PORT + 80,         #网关HTTP端口
        'adminport' : PORT + 1            #网关ADMIN端口，只会在localhost接口上监听
    }

#游戏区游戏服务器配置
GAMESERVER = {
        'server_id' : SERVER_ID + 10,     #游戏服务器编号
        'hostname'  : HOST_GAME,          #游戏服务器IP地址, 最好使用局域网，不要开放到外网
        'port'      : PORT + 10,          #游戏服务器TCP端口
        'adminport' : PORT + 11           #游戏服务器ADMIN端口，只会在localhost接口上监听
    }

#游戏区角色服务器配置
CHARACTERSERVER = {
        'server_id' : SERVER_ID + 20,     #角色服务器编号
        'hostname'  : HOST_CHARACTER,     #角色服务器TCP地址, 最好使用局域网，不要开放到外网
        'port'      : PORT + 20,          #角色服务器TCP端口
        'adminport' : PORT + 21           #角色服务器ADMIN端口，只会在localhost接口上监听
    }

#游戏区聊天服务器配置
MESSAGESERVER = {
        'server_id' : SERVER_ID + 30,     #聊天服务器编号
        'hostname'  : HOST_MESSAGE,       #聊天服务器TCP地址, 最好使用局域网，不要开放到外网
        'port'      : PORT + 30,          #聊天服务器TCP端口
        'adminport' : PORT + 31           #聊天服务器ADMIN端口，只会在localhost接口上监听
    }

#游戏区公会服务器配置
ALLIANCESERVER = {
        'server_id' : SERVER_ID + 40,     #聊天服务器编号
        'hostname'  : HOST_MESSAGE,       #聊天服务器TCP地址, 最好使用局域网，不要开放到外网
        'port'      : PORT + 40,          #聊天服务器TCP端口
        'adminport' : PORT + 41           #聊天服务器ADMIN端口，只会在localhost接口上监听
    }

#数值管理服务器配置, 正式服无需配置
ADMINSERVER = {
        'server_id' : SERVER_ID + 100,    #数值管理服务器编号
        'port'      : 8081,               #数值管理服务器HTTP端口
        'dbhost'    : '127.0.0.1',        #要管理的MySQL服务器TCP地址
        'dbport'    : 3306,               #要管理的MySQL服务器TCP端口
        'dbuser'    : 'root',             #MySQL服务器账号
        'dbpass'    : 'db1234',           #MySQL服务器密码
        'admindb'   : 'tc3dk_admin',      #数值管理自用database名称
        'accountdb' : 'tc3dk_account',    #游戏账号database名称
        'userdb'    : 'tc3dk_userdb',     #游戏角色database名称
        'pool_size' : 2,                  #连接池最大同时MySQL连接数
    }
