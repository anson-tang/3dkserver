#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

import time
import hashlib
import urllib
import urllib2

from bottle  import route, template, request
from utils   import print_e, http_json_get_sync, pprint
from hashlib import md5
from json    import dumps, loads

try:
    BASE_SESSION_HASH
except NameError:
    BASE_SESSION_HASH = hashlib.md5()
    BASE_SESSION_HASH.update('w2LKSDjjlsdli99uoj#@#')

def gm_sign(*args):    
    h = BASE_SESSION_HASH.copy()    
    h.update(''.join(map(str, args)))    
    return h.hexdigest()

def gm_post(host, port, uri, args):
    params = urllib.urlencode(args)
    URL = 'http://{0}:{1}/{2}'.format(host, port, uri)
    req    = urllib2.Request(URL, params)
    res    = urllib2.urlopen(req)
    return res.read()

global DATA
DATA = []

@route('/test')
def test():
    return template('test', data=DATA)


@route('/random_item', method="POST")
def random_item():
    try:
        global DATA
        cmd        = request.forms.cmd.strip()
        role_level = request.forms.role_level.strip()
        vip_level  = request.forms.vip_level.strip()
        count      = request.forms.count.strip()
        count      = count if count else 1
        args       = [role_level, vip_level, count]

        ts   = int(time.time())
        args = dumps(args)
        sign = gm_sign(cmd, ts, args)

        args = {'cmd':cmd, 'ts':ts, 'args':args, 'sign':sign}
        res  = gm_post('192.168.8.233', 28081, 'gm', args)
        res  = loads(res)
        if isinstance(res, list):
            DATA = res
        #pprint('cmd:', cmd, 'count:', args, 'res:', loads(res))
    except Exception, e:
        res = 'Exception', str(e)

    return template('test', data=DATA)


