#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import json
import hashlib

from datetime         import datetime
from twisted.internet import defer
from log              import log
from protocol_manager import gs_call
from manager.gateuser import g_UserMgr
from handler.gs       import send2client
from handler_gm       import server_login_user
from gm_errorno       import *
from gm_db            import db



FIELDS = 'orderno', 'account', 'cid', 'server_id', 'amount', 'charge_id', 'create_time', 'update_time', 'get_credits'

@defer.inlineCallbacks
def new_data(values):
    _sql = 'INSERT INTO tb_payment (' + ','.join(FIELDS) + ') VALUES (' + ','.join(['%s'] * len(values)) + ')'
    yield db.insert(_sql, values)

@defer.inlineCallbacks
def load_data(orderno):
    _sql = 'SELECT {0} FROM tb_payment WHERE orderno={1};'.format(','.join(FIELDS), orderno)

    _dataset = yield db.query(_sql)
    if _dataset:
        if _dataset[0][-1] > 0:
            defer.returnValue( (True, False) )
        else:
            defer.returnValue( (False, False) )

    defer.returnValue( (False, True) )

@defer.inlineCallbacks
def update_data(values):
    _sql = 'UPDATE tb_payment SET cid=%s,update_time=%s,get_credits=%s WHERE orderno=%s;'
    yield db.execute(_sql, values)

try:
    BASE_TOKEN_HASH
except NameError:
    BASE_TOKEN_HASH = hashlib.md5()

def check_sign(*args):
    h = BASE_TOKEN_HASH.copy()
    h.update(''.join(map(str, args)))
    return h.hexdigest()

@defer.inlineCallbacks
def htpayment(request):
    '''
    @param: charge_id-充值交易ID
    '''
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')
    log.info('[ payment ] request.args: {0}.'.format( request.args ))
    res_err = {'result': 1, 'extend': ''}

    if len(request.args) != 6:
        log.error("[ payment ] unknown args: {0}.".format( request.args ))
        res_err['result'] = -PAYMENT_ARGS_ERROR
        defer.returnValue( json.dumps( res_err ) )

    charge_id = int(request.args['order'][0])
    orderno = request.args['transaction'][0]
    account = request.args['user'][0]
    server_id = request.args['server'][0]
    amount    = request.args['amount'][0]
    sign      = request.args['salt'][0]

    repeat_flag, new_flag = yield load_data(orderno)
    log.info('repeat_flag: {0}, new_flag: {1}.'.format( repeat_flag, new_flag ))
    if repeat_flag:
        log.error("[ payment ] repeat orderno. args: {0}.".format( request.args ))
        res_err['result'] = -PAYMENT_ORDERNO_REPEAT
        defer.returnValue( json.dumps( res_err ) )

    if new_flag:
        yield new_data( [orderno, account, 0, server_id, amount, charge_id, datetime.now(), 0, 0] )

    log.info('[ payment ] charge_id:{0}, orderno:{1}, account:{2}, server_id:{3}, amount:{4}.'.format(charge_id, orderno, account, server_id, amount))

    #Check sign
    sign_local = check_sign(charge_id, orderno, account, server_id, amount, '2481ba98a91fca6')
    sign_local = sign_local[3:28]
    log.info("[ payment ] sign:{0}, sign_local:{1}.".format(sign, sign_local))

    if sign != sign_local:
        log.error("[ payment ] unknown sign:{0}, sign_local:{1}.".format(sign, sign_local))
        res_err['result'] = -PAYMENT_SIGN_ERROR
        defer.returnValue( json.dumps( res_err ) )

    try:
        err_login, cid = yield server_login_user( '%s%s'%(account, server_id) )
    except Exception as e:
        log.error("[ htpayment ] unknown error, account: {0}, e: {1}, args: {2}.".format( account, e, request.args ))
        res_err['result'] = -PAYMENT_USER_ERROR
        defer.returnValue( json.dumps(res_err) )

    if err_login or (not cid):
        log.error('[ payment ] unknown account: {0}, cid: {1}, args: {2}.'.format( account, cid, request.args ))
        res_err['result'] = -PAYMENT_USER_ERROR
        defer.returnValue( json.dumps(res_err) )

    # 预留的参数
    platform_id, parent_id, currency_type, currency = 1, 1, 1, 0
    try:
        res_data, credits_data = yield gs_call("payment_from_platfrom", (cid, orderno, charge_id, platform_id, parent_id, currency_type, currency))

        if not res_data:
            send2client(cid, 'sync_credits_added', credits_data[1:])
            # update sql data
            yield update_data( [cid, datetime.now(), credits_data[0], orderno] )
        else:
            log.error('[ payment ]result from gameserver. res_data:{0}, args: {1}.'.format(res_data, request.args))
            res_err['result'] = -PAYMENT_FAIL
            defer.returnValue( json.dumps(res_err) )
    except Exception, e:
        log.exception("[ payment ]gs_call error. account:{0}, charge_id:{1}, platform_id:{2}, parent_id:{3}, currency_type:{4}, currency:{5}, args:{6}.".format(
            account, charge_id, platform_id, parent_id, currency_type, currency, request.args))
        res_err['result'] = -PAYMENT_FAIL
        defer.returnValue( json.dumps(res_err) )

    defer.returnValue( json.dumps(res_err) )




