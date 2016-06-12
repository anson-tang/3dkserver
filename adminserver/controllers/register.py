#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle  import route, template, request
from utils   import print_e, http_json_get_sync, pprint
from hashlib import md5

import time

SERVERs = (
        ('公司内部', 'http://login.5xhb.com/openid/openid_regist'),
    )

REGISTER_ERROR = {
        -1001001: '参数错误',
        -1001002: '签名Key配置错误',
        -1001003: '签名错误',
        -2501001: '参数游戏编号错误',
        -2501002: '用户账号错误',
        -2501003: '密码错误',
        -2501021: '用户名不能包含特殊字符',
        -2501031: '游戏不存在',
        -2501032: '用户已存在',
        }

GAME_ID  = '3d3k'
SIGN_KEY = '8thke4b385gh76sj2df8'

def _generate_sign(username, t):
    sign_before_encode = '{0}{1}{2}{3}'.format(GAME_ID, username, t, SIGN_KEY)
    sign = md5(sign_before_encode).hexdigest()[2:30]
    return sign

@route('/register')
def regiter_view():
    return template('register', servers=[s[0] for s in SERVERs])

@route('/register', method="POST")
def register():
    user = request.forms.username.strip()
    #pwd  = md5(request.forms.password.strip()).hexdigest()
    pwd  = request.forms.password.strip()
    url  = SERVERs[int(request.forms.server.strip()) - 1][1]

    t    = int(time.time())
    sign = _generate_sign(user, t)

     
    try:
        result = http_json_get_sync(url, dict(game=GAME_ID, user=user, pwd=pwd, timestamp=t, sign=sign))
        if result['return_code'] == 1:
            return {'result':0, 'data':''}
        else:
            pprint("[ register ]", result)
            err = REGISTER_ERROR.get(result['return_code'], '未知错误')
            return {'result':result['return_code'], 'data':'{0}, detail:{1}'.format(err, result['return_msg'])}
    except Exception, e: 
        print_e()
        return {'result':1, 'data':str(e)}
      

