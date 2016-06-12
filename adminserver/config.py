#-*-coding: utf-8-*-

'''
@version: 0.2
@author: U{Don.Li<mailto: donne.cn@gmail.com>}
@license: Copyright(c) 2012 Don.Li

@summary:
'''

#import ConfigParser
#from os.path import normpath, dirname

conf            = None
port            = None
db_conf         = None
user_db         = None
redis_conf      = None

from setting import DB, REDIS

def init(server_name):
    global port, db_conf, user_db, redis_conf

    db_conf = {
        'dbuser'   : DB['user'],
        'dbpass'   : DB['pass'],
        'dbhost'   : DB['host'],
        'dbport'   : DB['port'],
        'dbname'   : DB['db_sysconfig'],
    }

    user_db = DB['db_userdb']

    redis_sock  = REDIS.get('redis_sock', None)
    if redis_sock:
        redis_conf = dict(
                unix_socket_path = redis_sock, 
                db   = REDIS['redis_db']
                )
    else:
        redis_conf = dict(
                host = REDIS['redis_host'],
                port = REDIS['redis_port'],
                db   = REDIS['redis_db']
                )

    #global conf, port, db_conf, admin_db, account_db, user_db, redis_conf

    #conf = ConfigParser.ConfigParser()
    #conf.readfp(open(normpath(dirname(__file__) + '/../etc/setting_env.py')))

    #port = conf.getint(server_name, 'port')

    #db_conf = {
    #    'dbuser'   : conf.get(   'DB', 'user'),
    #    'dbpass'   : conf.get(   'DB', 'pass'),
    #    'dbhost'   : conf.get(   'DB', 'host'),
    #    'dbport'   : conf.getint('DB', 'port'),
    #    'dbname'   : conf.get(   'DB' , 'db_sysconfig'),
    #}

    #user_db    = conf.get('DB', 'db_userdb')

    #try:
    #    redis_sock = conf.get('REDIS', 'redis_sock')
    #except ConfigParser.NoOptionError:
    #    redis_sock = None

    #if redis_sock:
    #    redis_conf = dict(
    #            unix_socket_path = redis_sock, 
    #            db   = conf.getint('REDIS', 'redis_db')
    #            )
    #else:
    #    redis_conf = dict(
    #            host = conf.get('REDIS', 'redis_host'),
    #            port = conf.getint('REDIS', 'redis_port'),
    #            db   = conf.getint('REDIS', 'redis_db')
    #            )

