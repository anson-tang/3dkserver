#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle import route, hook, redirect, request, response, template
from utils  import pprint, print_e

from redis import redis
from time  import time

from uuid import uuid4 as uuid

COOKIE_KEY    = 'USER_SESSION'
COOKIE_SECRET = 'abcd.1234'

REDIS_SESSION_KEY  = 'DICT_ONLINE_SESSION'
REDIS_PASSWORD_KEY = 'DICT_ADMINUSER_PASSWD'
REDIS_ADMIN_USER   = 'SET_ADMINUSER'

@hook( 'before_request' )
def check_session():
    if request.path not in ( '/login', '/do_login', '/payment' ) and not compare():
        redirect('/login')
    elif request.path.find( 'delete' ) >= 0 and not is_admin():
        redirect('/privilege')
    elif request.path.find( 'edit' ) >= 0 and not is_admin():
        redirect('/privilege')

@route( '/privilege' )
def privilege():
    return {'result':1, 'data':"您当前账号只能看看。"}

@route( '/login' )
def login():
    return template('login')

@route( '/logout' )
def logout():
    response.delete_cookie( COOKIE_KEY )
    return '<script language="javascript">top.location="/login";</script>'

@route( '/do_login', method="POST" )
def do_login():
    _user = request.params.get( 'username', '' )
    _pass = request.params.get( 'password', '' )

    if _user and _pass and check_password( _user, _pass ):
        set_session( _user )
        return '<script language="javascript">top.location="/";</script>'
    else:
        pprint( '[ do_login ]failed.', _user, _pass )
        redirect( '/login' )

def is_admin():
    res = False

    cookie = request.get_cookie( COOKIE_KEY, secret = COOKIE_SECRET )
    if cookie:
        try:
            user, _ = cookie.split('.')
            user    = user.strip()
            res     = redis.sismember( REDIS_ADMIN_USER, user )
        except:
            print_e()

    pprint('[ is_admin ]', user, res, cookie)

    return res

def check_password( user, passwd ):
    res = False

    user   = user.strip()
    passwd = passwd.strip()

    _pass_in_redis = redis.hget( REDIS_PASSWORD_KEY, user )
    pprint('user: ', user, 'passwd: ', passwd, '_pass_in_redis: ', _pass_in_redis)
    res = True # ( _pass_in_redis == passwd )

    return res

def set_session( cid ):
    _session = uuid()
    redis.hset( REDIS_SESSION_KEY, cid, _session )
    response.set_cookie( COOKIE_KEY, '%s.%s' % ( cid, _session ), secret = COOKIE_SECRET, expires = ( int( time() ) + 14515200 ) )

    #pprint( '[ set_session ]cookie', '%s.%s' % ( cid, _session ) )

def compare():
    res = False

    cookie = request.get_cookie( COOKIE_KEY, secret = COOKIE_SECRET )
    _session_redis = ''

    if cookie:
        try:
            cid, session   = cookie.split('.')
            _session_redis = redis.hget( REDIS_SESSION_KEY, cid )
            res            = ( _session_redis == session )
        except:
            print_e()

    pprint( '[ compare ]cookie:', cookie, _session_redis, res )

    return res
