#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle  import route, template, request
from utils   import print_e, http_json_get_sync, pprint
from hashlib import md5
from json import dumps, loads

import time

help_dic = {
        'modify_character_level' : '修改玩家等级, 请输入:[account] [target_level]',
        #'modify_character_level' : '[account] [target_level]',
        #'add_credits' : '[account] [add_credits]',
        #'add_items' : '[account] [item_type] [item_id] [add_count]' 
        'add_items' : '新增道具, 请输入:[account] [item_type] [item_id] [add_count]',
        }

svcs     = ('开发李服', '192.168.8.233', 11080, 1),\
           ('开发唐门', '192.168.8.233', 28081, 2),\
           ('DailyBuild', '192.168.8.233', 21080, 3),\
           ('开发黄松', '192.168.8.233', 14080, 13),\
           ('Stage[内]', '192.168.8.246', 22100, 4),\
           ('水泊梁山', '192.168.8.246', 28081, 1001)
#           ('策划服[岑岑]', '192.168.8.246', 23008), \
#           ('策划服[陈陈]', '192.168.8.246', 23102), \
#           ('策划服[段氏]', '192.168.8.246', 23208), \
#           ('策划服[郭蕾]', '192.168.8.246', 23308), \
#           ('策划服[李娜]', '192.168.8.246', 23408)

tuple_PlatformID2Index = (1, 0), (2, 1), (3, 2), (13, 3), (4, 4), (1001, 5)

def indexOfPid(pid):
    for _pid, idx in tuple_PlatformID2Index:
        if _pid == int(pid):
            return idx
    else:
        pprint("[ indexOfPid ]: Not found pid index. pid:", pid)
        return -1

@route('/gm')
def gm():
    return template('gm', svcs=svcs, help_dic=help_dic)

import hashlib
try:
    BASE_SESSION_HASH
except NameError:
    BASE_SESSION_HASH = hashlib.md5()
    BASE_SESSION_HASH.update('w2LKSDjjlsdli99uoj#@#')

@route('/payment', method="POST")
def payment_local():
    svc_idx = int(request.forms.svc.strip())
    account = request.forms.account.strip()
    charge_id = int(request.forms.charge_id.strip())
    server_id = int(request.forms.server_id.strip())

    host, port, server_id = svcs[indexOfPid(svc_idx)][1:]

    pprint('[ payment_local ]svc_idx:', svc_idx, 'svc host:', host, 'svc port:', port, 'account:', account, 'charge_id:', charge_id, 'server_id:', server_id)

    args = account, charge_id, server_id, 1, 1, 1, 0, int(time.time())

    sign = gm_sign(*args)

    require_args = args + (sign, )
    args = require_args # dumps(require_args)
    try:
        res = gm_post(host, port, 'payment', dict(args=dumps(args)))
    except Exception, e:
        res = 'Exception', str(e)
        print_e()
    pprint("Res of gm post:", res)

    return {'data':str(res)}

def gm_sign(*args):    
    h = BASE_SESSION_HASH.copy()    
    h.update(''.join(map(str, args)))    
    return h.hexdigest()

def gm_post(host, port, uri, args):
    import urllib, urllib2
    from json import dumps
    #params = urllib.urlencode(dict(args=dumps(args)))
    params = urllib.urlencode(args)
    URL = 'http://{0}:{1}/{2}'.format(host, port, uri)
    req    = urllib2.Request(URL, params)
    res    = urllib2.urlopen(req)
    return res.read()

@route('/exe_gm_cmd', method="POST")
def exe_gm_cmd():
    cmd_cmd = request.forms.cmd_cmd.strip()
    svc_idx = int(request.forms.svc.strip())
    cmd_args = (request.forms.cmd_args.strip()).split(' ')

    host, port, server_id = svcs[svc_idx][1:]
    cmd_args.append(server_id)

    pprint('cmd:', cmd_cmd, 'svc host:', host, 'svc port:', port, 'args:', cmd_args)
    ts = int(time.time())
    cmd_args = dumps(cmd_args)
    sign     = gm_sign(cmd_cmd, ts, cmd_args)

    args = {'cmd':cmd_cmd, 'ts':ts, 'args':cmd_args, 'sign':sign}

    #require_args = [cmd_cmd, 1, cmd_args, sign]
    #args = require_args # dumps(require_args)
    try:
        res = gm_post(host, port, 'gm', args)
    except Exception, e:
        res = 'Exception', str(e)

    pprint("Res of gm post:", res)
    return {'data':str(res)}
       
