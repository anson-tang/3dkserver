#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

from twisted.internet        import defer


from time     import time
from datetime import datetime
from log      import log
from marshal  import loads, dumps
from errorno  import *
from constant import *
from redis    import redis



@defer.inlineCallbacks
def get_daily_pay_record(character_id, pay_date=""):
    ''' return daily total pay.
    '''
    if not pay_date:
        pay_date = datetime.now().strftime("%Y-%m-%d")

    _data = yield redis.hget(HASH_DAILY_PAY_RECORD, pay_date)
    if _data:
        _data = loads(_data)
    else:
        _data = []

    for _cid, _cost in _data:
        if _cid == character_id:
            defer.returnValue( _cost )

    defer.returnValue( 0 )

@defer.inlineCallbacks
def add_daily_pay_record(character_id, add_cost):
    ''' new pay record.
    '''
    pay_date = datetime.now().strftime("%Y-%m-%d")
    # old pay record
    _data = yield redis.hget(HASH_DAILY_PAY_RECORD, pay_date)
    if _data:
        _data = loads(_data)
    else:
        _data = []

    # 新增豪华签到时间点
    _pay_login_data = yield redis.hget(HASH_PAY_LOGIN_PACKAGE, character_id)
    if not _pay_login_data:
        yield redis.hset(HASH_PAY_LOGIN_PACKAGE, character_id, dumps([int(time()), 1, 0]))

    _had_cost = add_cost
    for _record in _data:
        if _record[0] == character_id:
            _record[1] += add_cost
            _had_cost = _record[1]
            break
    else:
        _data.append( [character_id, add_cost] )

    # update pay record
    yield redis.hset(HASH_DAILY_PAY_RECORD, pay_date, dumps(_data))

    defer.returnValue( _had_cost )



