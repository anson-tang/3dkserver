#!/usr/bin/env python
# -*- coding: utf-8 -*-

from constant   import *
from gm_errorno import *
from twisted.internet import defer

import json

import hashlib

from log import log
from protocol_manager import gs_call
from manager.gateuser import g_UserMgr
from handler.gs       import send2client
from handler_gm       import base_gm_sign, server_login_user

@defer.inlineCallbacks
def payment(request):
    '''
    @param: charge_id-充值交易ID
    '''
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')

    args_data_raw = request.args['args']
    #log.info("[ payment ]args raw:{0}.".format(args_data_raw))

    if 0 == len(args_data_raw):
        log.error("[ payment ]unknown args raw:{0}.".format(args_data_raw))
        defer.returnValue( json.dumps( GM_INVALID_CMD ) )

    cmd_info = json.loads(args_data_raw[0])

    if len(cmd_info) != 9:
        log.err("[ payment ]unknown cmd_info:{0}.".format(args_data_raw[0]))
        defer.returnValue( json.dumps( GM_INVALID_CMD ) )

    account, charge_id, server_id, platform_id, parent_id, currency_type, currency, t, sign = cmd_info
    log.info('[ payment ]account:{0}, charge_id:{1}, platform_id:{2}, parent_id:{3}, currency_type:{4}, currency:{5}, t:{6}, sign:{7}, server_id:{8}'.format(account, charge_id, platform_id, parent_id, currency_type, currency, t, sign, server_id) )

    #Check base_gm_sign later
    sign_local = base_gm_sign(*cmd_info[:-1])

    if sign != sign_local:
        log.error("[ payment ]unknown sign:{0}, correct sign:{1}.".format(sign, sign_local))
        defer.returnValue( json.dumps( GM_INVALID_SIGN ) )

    try:
        res_login = yield server_login_user( '%s%s'%(account,server_id) )
    except Exception as e:
        log.error("[ payment ]unknown error, e: {0}.".format( e ))
        defer.returnValue(json.dumps(GM_EXECUTE_FAIL))

    err_login, cid = res_login
    if 0 != err_login:
        log.error("[ payment ]unknown error. account:{0}, cid:{1}, error no:{2}.".format(account, cid, err_login))
        defer.returnValue(json.dumps(GM_LOGIN_USER_FAIL))

    try:
        res_data, credits_data = yield gs_call("payment_from_platfrom", (cid, '', charge_id, platform_id, parent_id, currency_type, currency))

        if not res_data:
            _user  = g_UserMgr.getUserByCid(cid)
            if _user:
                send2client(cid, 'sync_credits_added', credits_data[1:])
                log.info('[ payment ] credits_data: {0}.'.format( credits_data ))
        else:
            log.error('[ payment ]result from gameserver. res_data:{0}.'.format(res_data))
            defer.returnValue( json.dumps(res_data) )
    except Exception, e:
        log.exception("[ payment ]gs_call error. account:{0}, charge_id:{1}, platform_id:{2}, parent_id:{3}, currency_type:{4}, currency:{5}".format(
            account, charge_id, platform_id, parent_id, currency_type, currency))
        defer.returnValue( json.dumps(GM_EXECUTE_FAIL) )

    defer.returnValue( json.dumps(0) )


