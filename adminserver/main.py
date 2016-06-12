#-*-coding:utf-8-*-

import initenv

from bottle import run, install, default_app
import sys

import config

def start(server):
    config.init(server.upper())

    from bottle_mysql import MySQLPlugin
    import controllers
    install(MySQLPlugin(**config.db_conf))
    run(host="0.0.0.0", port=config.port, debug=True, reloader=True, server='twisted')

def stop(s, f):
    pass

def reload_config(s, f):
    pass

def open_login_server(s, f):
    pass

def stop_login_server(s, f):
    pass

if __name__ == '__main__':
    start('adminserver')
else:
    config.init('ADMINSERVER')

    from bottle_mysql import MySQLPlugin
    import controllers
    install(MySQLPlugin(**config.db_conf))

    application = default_app()
