#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 


import json

from twisted.internet import defer
from log              import log
from redis            import redis
from constant         import *



DESC_FILE = 'etc/resource_v%s.py'

@defer.inlineCallbacks
def reload_resource(request):
    ''' 加载新的资源 '''
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')
    res_err = {'res_url':'', 'reward_status':0, 'total_size':0, 'folder_name':''}

    if len(request.args) < 3:
        log.error('Request args error. args: {0}.'.format( request.args ))
        defer.returnValue( json.dumps(res_err) )

    ver_res     = request.args['ver_res'][0]
    ver_game    = request.args['ver_game'][0]
    device_type = request.args['device_type'][0]
    accountname = request.args['accountname'][0]
    server_id   = request.args['server_id'][0]

    cid   = yield redis.hget(DICT_ACCOUNT_REGISTERED, '%s%s'%(accountname,server_id))
    if not cid:
        log.error('Unknown account. args: {0}.'.format( request.args ))
        defer.returnValue( json.dumps(res_err) )

    try:
        with open(DESC_FILE%ver_game) as desc_file:
            desc_info = json.loads(desc_file.read())
            desc_file.close()
    except Exception, e:
        log.error('Error. e: {0}.'.format( e ))
        defer.returnValue( json.dumps(res_err) )

    ver_curr_res = desc_info.get('VER_CURR_RES', 0)
    zip_name = 'r%s_to_%s.zip'%(ver_res, ver_curr_res)
    if not desc_info.has_key(zip_name):
        log.error('Error. desc_info: {0}, zip_name: {1}.'.format( desc_info.keys(), zip_name ))
        defer.returnValue( json.dumps(res_err) )

    # 获取更新资源的奖励状态
    flag = yield redis.hexists(HASH_RESOURCE_REWARD, cid)
    if not flag:
        res_err['reward_status'] = 1

    #res_err['res_url'] = "http://192.168.8.233/%s"%(zip_name)
    res_err['res_url'] = "%s/%s"%(RESOURCE_ANDROIS_URLBASE, zip_name)
    res_err['total_size']  = desc_info[zip_name]
    res_err['folder_name'] = 'r%s_to_%s'%(ver_res, ver_curr_res)

    defer.returnValue( (json.dumps(res_err)) )



