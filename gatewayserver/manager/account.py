#!/usr/bin/env python
#-*- coding: utf-8-*-

from time import time
from urllib import urlencode
from twisted.internet.defer import inlineCallbacks, returnValue

from errorno import NET_ERROR, LOGIN_PARAMS_ERR
from hashlib import md5

from twisted.internet import defer
from log import log

from constant import TIPCAT_CID, TIPCAT_GAME_ID, TIPCAT_LOGIN_SECURITY_ID, TIPCAT_LOGIN_URLBASE, HEITAO_LOGIN_URLBASE, HEITAO_CID
from json import loads

from http import HttpRequestHelper
httphelper = HttpRequestHelper()

def _generate_sign(username, t):
    sign_before_encode = '{0}{1}{2}{3}'.format(TIPCAT_GAME_ID, username, t, TIPCAT_LOGIN_SECURITY_ID)
    sign = md5(sign_before_encode).hexdigest()[2:30]
    return sign

def tipcat_login_url(user, sessionkey):
    ts = int(time())
    #salt = gen_salt(TIPCAT_GAME_ID, user, ts, TIPCAT_LOGIN_SECURITY_ID)
    sign = _generate_sign(user, ts)

    q = urlencode(dict(game=TIPCAT_GAME_ID, user=user, sessionkey=sessionkey, timestamp=ts, sign=sign))
    return '%s?%s' % (TIPCAT_LOGIN_URLBASE, q)


def tipcat_login_parse(user, data):
    d = loads(data)
    return d.get('return_code') == 1


def nd_91_login_url(user, sessionkey):
    salt = gen_salt(ND_91_APPID, ND_91_LOGIN_ACT, user, sessionkey, ND_91_APPKEY)
    q = urlencode(dict(AppId=ND_91_APPID, Act=ND_91_LOGIN_ACT, Uin=user, SessionId=sessionkey, Sign=salt))
    return '%s?%s' % (ND_91_URLBASE, q)


def nd_91_login_parse(user, data):
    d = loads(data)
    return d.get('ErrorCode') == '1'

def heitao_login_url(user, sessionkey):
    q = urlencode(dict(uid=user, token=sessionkey))
    return '%s?%s' % (HEITAO_LOGIN_URLBASE, q)

def heitao_login_parse(user, data):
    d = loads(data)
    return d.get('errno') == 0



CID_URL_RESULT = {
    TIPCAT_CID: (tipcat_login_url, tipcat_login_parse),
    HEITAO_CID: (heitao_login_url, heitao_login_parse),
}


@inlineCallbacks
def login_check(cid, user, sessionkey):
    result, reason = 0, 0
    # 除了tipcat外 就是heitao
    if cid != TIPCAT_CID:
        cid = HEITAO_CID

    if cid in CID_URL_RESULT:
        login_url, login_parse = CID_URL_RESULT[cid]
        url = login_url(user, sessionkey)
        try:
            data = yield httphelper.request(url, 'POST')
            result = login_parse(user, data)
        except Exception, e:
            reason = NET_ERROR
            log.warn('ACC WEB ERR', cid, url, e)
    else:
        reason = LOGIN_PARAMS_ERR

    returnValue((result, reason, ''))


