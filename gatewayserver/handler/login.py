#!/usr/bin/env python
#-*- coding: utf-8-*-

import config

from rpc   import route
from time  import time
from redis import redis

from twisted.internet import defer
from manager.account  import login_check
from constant         import *
from errorno          import *
from log              import log

from manager.gateuser import g_UserMgr
from protocol_manager import gs_call, protocol_manager, ms_call, alli_call, gs_send
from handler          import gm


@route()
@defer.inlineCallbacks
def login(p, req):
    res = [UNKNOWN_ERROR, [None, int(time()), config.httport, [0, 0], -1] ]

    log.warn('Login args: {0}.'.format( req ))
    if len(req) == 6:
        login_type, platform_id, accountname, session_key, version, sid = req
    else:
        login_type, accountname, session_key, version, sid = req
        platform_id = TIPCAT_CID

    #当服务器没有开启，且该账号不在AdminUser集合内，提示玩家服务器未开放
    if not gm.opened:
        _is_admin_user = yield redis.sismember( SET_GM_USER, accountname )
        if not _is_admin_user:
            res[0] = SERVER_IS_CLOSED
            defer.returnValue( res )

    # 检查客户端版本号 低于当前版本不能登录/注册
    _ver_status = check_client_version(version)
    if _ver_status:
        res[0] = _ver_status
        defer.returnValue( res )

    accountname = accountname.strip()
    session_key = session_key.strip()

    if len(accountname) == 0:
        log.error('Invalid account!')
        res[0] = UNKNOWN_CHAR
        defer.returnValue( res )
    elif len(session_key) == 0:
        log.error('Invalid session key!')
        res[0] = SESSION_NOT_VALID
        defer.returnValue( res )

    #try:
    #    res_sk = yield login_check(int(platform_id), accountname, session_key)
    #    log.debug('Result of login check:', res_sk)
    #    if not res_sk[0]:
    #        res[0] = SESSION_NOT_VALID
    #        log.error('Invalid session_key. accountname: {0}, session_key: {1}.'.format( accountname, session_key ))
    #        defer.returnValue( res )
    #except Exception as e:
    #    log.error('exception. e: {0}, accountname: {1}, session_key: {2}.'.format( e, accountname, session_key ))
    #    res[0] = SESSION_NOT_VALID
    #    defer.returnValue( res )

    p.account = accountname
    p.session_key = session_key

    cid   = yield redis.hget(DICT_ACCOUNT_REGISTERED, '%s%s'%(accountname,sid))
    if not cid:
        res[0] = LOGIN_NO_CHARACTER
        defer.returnValue( res )
    else:
        cid = int( cid )
    # 检查该玩家是否被封号
    _status = yield check_character_forbidden( cid )
    if _status:
        res[0] = CHAR_IN_FORBIDDEN
        defer.returnValue( res )

    try:
        result, char_data, version_conf = yield protocol_manager.gs_call("gs_login", (cid, version))
        if result:
            log.error('user login gameserver error. cid: {0}.'.format( cid ))
            res[0] = result
            defer.returnValue( res )
    except Exception as e:
        log.error('error. e: {0}.'.format( e ))
        defer.returnValue( res )

    char_data['cid']  = cid
    char_data['id']   = cid
    char_data['session'] = p.session_key
    char_data['sid']     = config.server_id

    end_cd_time = yield redis.hget(HASH_SCENE_COOLDOWN_TIME, cid)
    char_data['end_cd_time'] = int( end_cd_time or 0 )
    # 竞技场排名 0-没有排名
    _char_rank = yield redis.zscore( SET_ARENA_CID_RANK, cid )
    _char_rank = int(_char_rank) if _char_rank else 0
    try:
        alli_res, alliance_info = yield alli_call('alli_login', (cid, char_data['nick_name'], char_data['level'], char_data['vip_level'], char_data['might'], _char_rank, char_data['lead_id']))
        if alliance_info[0] > 0:
            gs_send('gs_alliance_info', (cid, alliance_info))
    except:
        alli_res = 1
        log.exception()
        alliance_info = 0, '', 0
    if alli_res:
        log.error('user login allianceserver error. cid: {0}.'.format( cid ))

    try:
        result = yield ms_call('ms_login', (cid, char_data['nick_name'], char_data['lead_id'], \
                char_data['vip_level'], char_data['level'], char_data['might'], alliance_info))
        if result:
            log.error('user login messageserver error. cid: {0}, result: {1}.'.format( cid, result ))
    except Exception as e:
        log.error('Login messageserver error. e: {0}.'.format( e ))

    # 获取天神领取的状态
    end_timestamp = yield redis.hget(HASH_RESCUE_ER_LANG_GOD, cid)
    end_timestamp = end_timestamp if end_timestamp else 0

    # 检查账号是否有重复登录, char_data已从gameserver重新获取
    _user_logined = g_UserMgr.getUserLogined(cid, p, session_key, info=char_data)
    if _user_logined:
        log.warn('user id({0}) have logined.'.format( cid ))
        res = NO_ERROR, (_user_logined.info, int(time()), config.httport, version_conf, end_timestamp)
        defer.returnValue( res )

    g_UserMgr.loginUser(p, cid, session_key, accountname, char_data)

    res = result, (char_data, int(time()), config.httport, version_conf, end_timestamp)
    defer.returnValue( res )

@route()
@defer.inlineCallbacks
def register(p, req):
    global REGISTER_ACCOUNTs
    res_err = [REGISTER_FAIL_ERROR, [None, int(time()), config.httport, 0] ]

    _account = getattr(p, 'account', None)
    if not _account:
        log.error('User no account info. from:', p.transport.getPeer())
        p.transport.loseConnection()
        defer.returnValue( res_err )

    if len(req) == 6:
        lead_id, nick_name, login_type, platform_id, version, sid = req
    else:
        lead_id, nick_name, sid = req
        login_type, platform_id, version = 0, '', ''
    
    # 判断昵称是否已被使用
    had_cid = yield redis.hget(DICT_NICKNAME_REGISTERED, nick_name)
    if had_cid:
        res_err[0] = LOGIN_REPEAT_NAME
        log.error('The nick_name had been used. had_cid: {0}, nick_name: {1}.'.format( had_cid, nick_name ))
        defer.returnValue( res_err )

    # 判断账号是否已注册
    had_cid = yield redis.hget(DICT_ACCOUNT_REGISTERED, '%s%s'%(_account,sid))
    if had_cid:
        log.warn('The account<{0}> had registered.'.format( _account ))
        res_err[0] = REGISTER_REQUEST_REPEAT
        defer.returnValue( res_err )

    # 判断是否正在注册ing
    if REGISTER_ACCOUNTs.has_key( _account ):
        log.warn('The nick_name<{0}> doing register.'.format( nick_name ))
        res_err[0] = REGISTER_REQUEST_REPEAT
        defer.returnValue( res_err )
    else:
        REGISTER_ACCOUNTs[_account] = 1

    try:
        err, char_data = yield protocol_manager.gs_call("gs_create_char", [lead_id, nick_name, _account, login_type, platform_id, version, int(sid)])
    except Exception as e:
        log.warn('gs_create_char error. e:', e)
        if REGISTER_ACCOUNTs.has_key( _account ):
            del REGISTER_ACCOUNTs[_account]
        defer.returnValue(res_err)

    if not err:
        cid  = char_data['id']
        user = g_UserMgr.getUserByCid( cid )
        if user:
            log.error('Use had existed! cid:', cid)
            if REGISTER_ACCOUNTs.has_key( _account ):
                del REGISTER_ACCOUNTs[_account]
            defer.returnValue( res_err )

        char_data['cid']     = char_data['id']
        char_data['session'] = p.session_key
        char_data['sid']     = config.server_id

        end_cd_time = yield redis.hget(HASH_SCENE_COOLDOWN_TIME, cid)
        char_data['end_cd_time'] = int( end_cd_time or 0 )

        try:
            _char_rank = 0
            try:
                alli_res, alliance_info = yield alli_call('alli_login', (cid, char_data['nick_name'], char_data['level'], char_data['vip_level'], char_data['might'], _char_rank, char_data['lead_id']))
            except:
                alli_res = 1
                log.exception()
                alliance_info = 0, '', 0

            if alli_res:
                log.error('user login allianceserver error. cid: {0}.'.format( cid ))

            result = yield ms_call('ms_login', (cid, char_data['nick_name'], char_data['lead_id'], char_data['vip_level'], char_data['level'], char_data['might'], alliance_info))
            if result:
                log.error('user login messageserver error. cid: {0}, result: {1}.'.format( cid, result ))
        except Exception as e:
            log.error('Login messageserver error. e: {0}.'.format( e ))

        g_UserMgr.loginUser(p, cid, p.session_key, _account, char_data)
 
        yield redis.hset(DICT_ACCOUNT_REGISTERED, '%s%s'%(_account,sid), char_data['cid'])
        yield redis.hset(DICT_NICKNAME_REGISTERED, nick_name, char_data['cid'])
        yield redis.sadd(SET_CID_REGISTERED, char_data['cid'])

        if REGISTER_ACCOUNTs.has_key( _account ):
            del REGISTER_ACCOUNTs[_account]
        defer.returnValue( [err, [char_data, int(time()), config.httport, 0]] )

    if REGISTER_ACCOUNTs.has_key( _account ):
        del REGISTER_ACCOUNTs[_account]
    defer.returnValue(res_err)

@route()
def logout(p, req):
    res = UNKNOWN_ERROR, []
    cid = p.cid

    g_UserMgr.logoutUser(cid)
    #log.debug('user logout. cid: {0}.'.format( cid ))
    return (NO_ERROR, [])

@route()
def reconnect(p, req):
    cid, sk = req
    log.debug('request reconnect. cid: {0}.'.format( cid ))
    return g_UserMgr.reconnectUser(p, cid, sk)
    #if g_UserMgr.reconnectUser(p, cid, sk):
    #    return NO_ERROR
    #else:
    #    return RECONNECT_FAIL

@route()
def online_notice(p, req):
    pass
    #return (NO_ERROR, [])

@defer.inlineCallbacks
def check_character_forbidden(cid):
    ''' return 0-未封号, 1-封号中
    '''
    _status = 0
    _time_now = int(time())
    _end_timestamp = yield redis.hget(HASH_SERVER_FORBIDDEN, cid)
    if _end_timestamp is None:
        pass
    elif _end_timestamp < 0:
        _status = 1
    elif _end_timestamp > _time_now:
        _status = 1
    else:
        yield redis.hdel(HASH_SERVER_FORBIDDEN, cid)

    defer.returnValue( _status )

def check_client_version(version):
    ''' 检查客户端版本 临时的, 限制低于v0.3.8.0的版本
    @return: 11-低于当前版本 0-等于或高于当前版本
    '''
    global LIMIT_VERSION
    if not version:
        log.error('Version error. cur: {0}, limit: {1}.'.format( version, LIMIT_VERSION ))
        return CLIENT_VERSION_ERROR

    try:
        _ver_client = map(int, version.split('.'))
        if len(_ver_client) < 4:
            log.error('Version error. cur: {0}, limit: {1}.'.format( version, LIMIT_VERSION ))
            return CLIENT_VERSION_ERROR

        for _k, _v in enumerate(_ver_client):
            if _v > LIMIT_VERSION[_k]:
                return NO_ERROR
            elif _v < LIMIT_VERSION[_k]:
                log.error('Version error. cur: {0}, limit: {1}.'.format( version, LIMIT_VERSION ))
                return CLIENT_VERSION_ERROR
        return NO_ERROR
    except Exception, e:
        log.exception()
        return NO_ERROR

def updte_limit_version(version):
    global LIMIT_VERSION
    LIMIT_VERSION = version

    return NO_ERROR


# all doing register account
REGISTER_ACCOUNTs = {}
# 限制的版本号
LIMIT_VERSION = [0, 3, 8, 0]



