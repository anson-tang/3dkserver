#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 


from time     import time
from rpc      import route
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps

from twisted.internet     import defer
from manager.messageuser  import g_UserMgr
from protocol_manager     import gw_send



@route()
@defer.inlineCallbacks
def mail_list(p, req):
    ''' 分页获取邮件列表 
    page_type: 1:全部; 2:好友; 3:系统; 4:战斗
    '''
    cid, [page_type, index] = req

    user = g_UserMgr.getUserByCid(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    user.notify_mail = False
 
    all_types  = []
    now_time   = int(time())
    mails_time = [] # for sort
    all_mails  = []

    if page_type == MAIL_PAGE_ALL:
        all_types = [MAIL_PAGE_FRIEND, MAIL_PAGE_SYSTEM, MAIL_PAGE_BATTLE]
    else:
        all_types = [page_type]

    for _type in all_types:
        # 每个type 最多保存100条 
        del_mail   = [] # 已过期的邮件ID
        _all = yield redis.hgetall( HASH_MAIL_CONTENT % (_type, cid) )
        for _field, _value in _all.iteritems():
            if _field == MAIL_PRIMARY_INC:
                continue
            _value = loads(_value)

            # 判断邮件是否过期
            if _value[1] + MAIL_VALID_SECONDS < now_time:
                del_mail.append( _field )
                continue
            # 根据时间点先后组织数据
            for _i, _time in enumerate(mails_time):
                if _value[1] > _time:
                    all_mails.insert(_i, _value)
                    break
            else:
                _i = len(mails_time)
                all_mails.append( _value )
            mails_time.insert(_i, _value[1])

        if del_mail:
            yield redis.hdel( HASH_MAIL_CONTENT % (_type, cid), *del_mail )

    defer.returnValue( (page_type, index, len(all_mails), all_mails[index:index+10]) )


@route()
@defer.inlineCallbacks
def write_mail(p, req):
    ''' 保存新的邮件 
    page_type: 1:全部; 2:好友; 3:系统; 4:战斗
    '''
    try:
        rcv_cid, page_type, module_id, detail = req
        send_time = int(time())
    except:
        rcv_cid, page_type, module_id, detail, send_time = req

    _key = HASH_MAIL_CONTENT % (page_type, rcv_cid )
    _primary = yield redis.hincrby( _key, MAIL_PRIMARY_INC, 1 )
 
    content = dumps( (_primary, send_time, page_type, module_id, detail) )
    yield redis.hset(_key, _primary, content)

    # 最多保存100条 
    _del_fields = []

    _all_fields = yield redis.hkeys( _key )
    _all_fields = sorted( _all_fields, reverse=True )
    if len(_all_fields) > 101:
        _del_fields = _all_fields[101:]
        if MAIL_PRIMARY_INC in _del_fields:
            _del_fields.remove( MAIL_PRIMARY_INC )

    if _del_fields:
        yield redis.hdel( _key, *_del_fields )

    # 通知在线玩家有新邮件
    rcv_user = g_UserMgr.getUserByCid(rcv_cid)
    if rcv_user and not rcv_user.notify_mail:
        rcv_user.notify_mail = True
        gw_send(rcv_cid, 'new_mail_notify', None)




