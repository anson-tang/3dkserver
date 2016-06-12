#!/usr/bin/env python
#-*- coding: utf-8 -*-

import json
import hashlib
import re
import copy
import marshal

from time                  import time
from constant              import *
from gm_errorno            import *
from twisted.internet      import defer
from redis                 import redis
from log                   import log
from manager.gateuser      import g_UserMgr
from protocol_manager      import gs_call
from handler_default       import DecimalEncoder
#from gm_db                 import db
from utils                 import timestamp2string
from handler.broadcast_msg import curr_broadcast_messages, sync_broadcast_messages



try:
    BASE_SESSION_HASH
except NameError:
    BASE_SESSION_HASH = hashlib.md5()
    BASE_SESSION_HASH.update('w2LKSDjjlsdli99uoj#@#')

try:
    HEITAO_SESSION_HASH
except NameError:
    HEITAO_SESSION_HASH = hashlib.md5()
    HEITAO_SESSION_HASH.update('Sd(-@FqMOTZBf')


def base_gm_sign(*args):
    h = BASE_SESSION_HASH.copy()
    h.update(''.join(map(str, args)))
    return h.hexdigest()

def heitao_gm_sign(*args):
    h = HEITAO_SESSION_HASH.copy()
    h.update(''.join(map(str, args)))
    return h.hexdigest()

@defer.inlineCallbacks
def server_login_user(account, character_id=None):
    if character_id:
        cid = character_id
    else:
        cid = yield redis.hget(DICT_ACCOUNT_REGISTERED, account)
        if not cid:
            defer.returnValue( (GM_INVALID_CID, 0) )
        else:
            cid = int( cid )

    user = g_UserMgr.getUserByCid( cid )
    if user:
        defer.returnValue( (0, cid) )

    try:
        errorno = yield gs_call("gs_gm_login", (cid, False))
        if errorno:
            defer.returnValue( (GM_INVALID_ERROR, 0) )
    except Exception as e:
        log.warn('Some exp raise when calling gs_offline_login(). e: {0}'.format(e))
        defer.returnValue( (GM_INVALID_ERROR, 0) )

    defer.returnValue( (0, cid) )

def server_logout_user(cid):
    # 通知在线玩家被踢的消息
    user = g_UserMgr.getUserByCid( cid )
    if user:
        try:
            if hasattr(user, 'p') and user.p:
                user.p.send('gm_kick_connect', None)
        except Exception, e:
            log.error('exception. cid: {0}, e: {1}.'.format( cid, e ))
    # 断开玩家socket连接
    g_UserMgr.kickoutUser( cid )

@defer.inlineCallbacks
def gm_modify_character_level(cmd, ts, args, sign):
    res_err = {'result': 1, 'level': 0}

    if len(args) != 2:
        defer.returnValue(GM_INVALID_ARGS)

    _cid   = int(args['character_id'])
    _level = int(args['character_level'])

    try:
        errorno = yield gs_call("gs_gm_login", (_cid, False))
        if errorno:
            res_err['result'] = errorno
            defer.returnValue(res_err)

        errorno, _final_level = yield gs_call('gs_gm_modify_character_level', [_cid, _level])
        if errorno:
            res_err['result'] = GM_INVALID_ERROR
        else:
            res_err['level'] = _final_level
    except Exception as e:
        log.error(' ERROR e:', e)
        log.exception()
        res_err['result'] = GM_INVALID_ERROR
        defer.returnValue(res_err)

    server_logout_user(_cid)

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_add_credits(cmd, ts, args, sign):
    if len(args) != 2:
        log.error('add credits error. args:{0}.'.format( args ))
        defer.returnValue(GM_INVALID_ARGS)

    account = args[0]
    add_credits = int( args[1] )

    try:
        res_login = yield server_login_user( account )
    except Exception as e:
        log.exception()
        defer.returnValue(GM_EXECUTE_FAIL)
    log.debug('Res of server_login_user:', res_login)
    err_login, cid = res_login
    if 0 != err_login:
        log.warn('Exp39287692 login user fail! account {0}, err_login {1}'.format( account, err_login ))
        defer.returnValue(GM_LOGIN_USER_FAIL)

    res = GM_EXECUTE_FAIL
    try:
        res = yield gs_call('gs_gm_add_credits', [ cid, add_credits ])
    except Exception as e:
        log.debug('Exp39380828 e:', e)
        log.exception()

    server_logout_user(cid)

    defer.returnValue( res )

@defer.inlineCallbacks
def gm_add_items(cmd, ts, args, sign):
    if len(args) != 5:
        log.error('add items error. args:{0}.'.format( args ))
        defer.returnValue(GM_INVALID_ARGS)

    account = args[0]
    item_type = int( args[1] )
    item_id = int( args[2] )
    add_count = int( args[3] )
    server_id = int( args[4] )

    try:
        res_login = yield server_login_user( '%s%s'%(account,server_id) )
    except Exception as e:
        log.exception()
        defer.returnValue(GM_EXECUTE_FAIL)
    log.debug('Res of server_login_user:', res_login)
    err_login, cid = res_login
    if 0 != err_login:
        log.error('user login fail! account {0}, err_login {1}'.format( account, err_login ))
        defer.returnValue(GM_LOGIN_USER_FAIL)

    res = GM_EXECUTE_FAIL
    try:
        res = yield gs_call('gs_gm_add_items', [ cid, item_type, item_id, add_count ])
        if not res[0]:
            quantity = 0
            for _, _, _, _num in res[1]:
                quantity += _num
            res[1] = quantity
    except Exception as e:
        log.error('exception. cid: {0}, e: {1}.'.format(cid, e) )
        log.exception()

    server_logout_user( cid )

    defer.returnValue( res )

@defer.inlineCallbacks
def gm_online_realtime_data(cmd, ts, args, sign):
    _data = {}
    _data['online_cnt'] = g_UserMgr.online_cnt
    _data['today_register_cnt'] = 0
    _data['register_cnt']  = yield redis.hlen(DICT_NICKNAME_REGISTERED)
    _data['today_pay_cnt'] = 0
    _data['pay_cnt'] = 0

    res_err = {'result': 1, 'realtime_data': _data}

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_search_character(cmd, ts, args, sign):
    res_err = {'result': 1, 'character_info': []}

    if len(args) != 1:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _infos = []
    _target_nickname = args['nick_name']
    _all_datas = yield redis.hgetall(DICT_NICKNAME_REGISTERED)
    pattern = re.compile(_target_nickname)
    for _nickname, _cid in _all_datas.iteritems():
        if not _nickname:
            continue
        if isinstance(_nickname, unicode):
            pass
        elif isinstance(_nickname, str):
            pass
        elif isinstance(_nickname, int):
            _nickname = str(_nickname)
        else:
            log.info('type: {0}.'.format( type(_nickname) ))
            continue

        match = pattern.search(_nickname)
        if not match:
            continue
        #else:
        #    log.info('match.group: {0}.'.format( match.group() ))
        #log.info('For Test. _nickname: {0}, _target_nickname: {1}.'.format( _nickname, _target_nickname ))
        _level, _online = 0, 0
        user = g_UserMgr.getUserByCid( _cid )
        if user:
            _level  = user.info.get('level', 0)
            _online = 1

        _infos.append( {'character_id': _cid, 'nick_name': _nickname, 'level': _level, 'online': _online} )
    
    res_err['character_info'] = _infos
    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_character_info(cmd, ts, args, sign):
    res_err = {'result': 1, 'character_info': {}}

    if len(args) != 1:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _cid = int(args['character_id'])

    _dict_data = {}
    user = g_UserMgr.getUserByCid( _cid )
    if user:
        _dict_data = copy.deepcopy(user.info)
        if user.temp_lost:
            _dict_data['online'] = 0
        else:
            _dict_data['online'] = 1
    else:
        try:
            errorno = yield gs_call("gs_gm_login", (_cid, True))
            if errorno:
                res_err['result'] = GM_INVALID_CID
                defer.returnValue( res_err )

            _dict_data = yield gs_call('gs_gm_get_character_info', [_cid])
            _dict_data['online'] = 0
        except Exception as e:
            log.exception()
            res_err['result'] = GM_INVALID_ERROR
            defer.returnValue( res_err )

    _dict_data['register_time'] = timestamp2string( _dict_data['register_time'] )
    _dict_data['last_login_time'] = timestamp2string( _dict_data['last_login_time'] )

    _dict_data['forbidden_seconds'] = yield check_character_status(_cid, TYPE_FORBIDDEN)
    _dict_data['mute_seconds'] = yield check_character_status(_cid, TYPE_MUTE)

    res_err['character_info'] = _dict_data
    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_camp_info(cmd, ts, args, sign):
    ''' 查询玩家的阵容信息 '''
    res_err = {'result': 1, 'camp_info': []}

    if len(args) != 1:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _cid = int(args['character_id'])

    try:
        errorno = yield gs_call("gs_gm_login", (_cid, True))
        if errorno:
            res_err['result'] = errorno
            defer.returnValue(res_err)

        _camp_info = yield gs_call('gs_gm_get_camp_info', [_cid])
        res_err['camp_info'] = _camp_info
    except Exception as e:
        log.error(' ERROR e:', e)
        log.exception()
        res_err['result'] = GM_INVALID_ERROR
        defer.returnValue(res_err)

    defer.returnValue(res_err)

@defer.inlineCallbacks
def gm_bag_info(cmd, ts, args, sign):
    ''' 查询玩家的背包物品 '''
    res_err = {'result': 1, 'bag_info': []}

    if len(args) != 2:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _cid      = int(args['character_id'])
    _bag_type = int(args['bag_type'])

    try:
        errorno = yield gs_call("gs_gm_login", (_cid, True))
        if errorno:
            res_err['result'] = errorno
            defer.returnValue(res_err)

        _bag_info = yield gs_call('gs_gm_get_bag_info', [_cid, _bag_type])
        res_err['bag_info'] = _bag_info
    except Exception as e:
        log.exception()
        res_err['result'] = GM_INVALID_ERROR
        defer.returnValue(res_err)

    defer.returnValue(res_err)

@defer.inlineCallbacks
def gm_character_status(cmd, ts, args, sign):
    ''' 查询服务器上的封号&禁言玩家 
    @param: type 1-封号 2-禁言
    '''
    res_err = {'result': 1, 'character_ids': []}

    if len(args) != 1:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _type = int(args['query_type'])
    _time_now = int(time())
    if _type == TYPE_FORBIDDEN:
        _all_datas = yield redis.hgetall( HASH_SERVER_FORBIDDEN )
        if not _all_datas:
            defer.returnValue( res_err )

        for _cid, _end_timestamp in _all_datas.iteritems():
            _temp = {'character_id': _cid, 'seconds': 0}
            if _end_timestamp < 0:
                _temp['seconds'] = -1
            elif _end_timestamp > _time_now:
                _temp['seconds'] = _end_timestamp - _time_now
            else:
                continue
            res_err['character_ids'].append( _temp )
    elif _type == TYPE_MUTE:
        _all_datas = yield redis.hgetall( HASH_SERVER_MUTE )
        if not _all_datas:
            defer.returnValue( res_err )

        for _cid, _end_timestamp in _all_datas.iteritems():
            _temp = {'character_id': _cid, 'seconds': 0}
            if _end_timestamp < 0:
                _temp['seconds'] = -1
            elif _end_timestamp > _time_now:
                _temp['seconds'] = _end_timestamp - _time_now
            else:
                continue
            res_err['character_ids'].append( _temp )
    else:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    defer.returnValue( res_err )

@defer.inlineCallbacks
def check_character_status(cid, query_type):
    ''' 检查服务器上的某玩家禁言/封号剩余秒数 '''

    _seconds  = 0
    if query_type == TYPE_FORBIDDEN:
        redis_key = HASH_SERVER_FORBIDDEN
    elif query_type == TYPE_MUTE:
        redis_key = HASH_SERVER_MUTE
    else:
        defer.returnValue( _seconds )

    _time_now = int(time())
    _end_timestamp = yield redis.hget(redis_key, cid)
    if _end_timestamp is None:
        pass
    elif _end_timestamp < 0:
        _seconds = -1
    elif _end_timestamp > _time_now:
        _seconds = _end_timestamp - _time_now

    defer.returnValue( _seconds )

@defer.inlineCallbacks
def gm_character_mute(cmd, ts, args, sign):
    ''' 对服务器上的某玩家禁言 '''
    res_err = {'result': 1, 'seconds': 0}

    if len(args) != 2:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _time_now = int(time())

    _cid, _seconds = int(args['character_id']), int(args['seconds'])
    if _seconds < 0:
        _end_timestamp = -1
    else:
        _end_timestamp = _time_now+_seconds
    yield redis.hset(HASH_SERVER_MUTE, _cid, _end_timestamp)
    res_err['seconds'] = _seconds

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_character_forbidden(cmd, ts, args, sign):
    ''' 对服务器上的某玩家封号 '''
    res_err = {'result': 1, 'seconds': 0}

    if len(args) != 2:
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( res_err )

    _time_now = int(time())

    _cid, _seconds = int(args['character_id']), int(args['seconds'])
    if _seconds < 0:
        _end_timestamp = -1
    else:
        _end_timestamp = _time_now+_seconds
    yield redis.hset(HASH_SERVER_FORBIDDEN, _cid, _end_timestamp)
    res_err['seconds'] = _seconds

    defer.returnValue( res_err )

def gm_character_kick(cmd, ts, args, sign):
    """ 踢玩家下线 """
    res_err = {'result': 1}

    if len(args) != 1:
        res_err['result'] = GM_INVALID_ARGS
        return res_err

    _cid = int(args['character_id'])

    user = g_UserMgr.getUserByCid( _cid )
    if not user or user.temp_lost:
        res_err['result'] = GM_CID_HAD_OFFLINE
        return res_err

    # 切断玩家的连接
    server_logout_user( _cid )
    return res_err

@defer.inlineCallbacks
def gm_grant_items_to(cmd, ts, args, sign):
    """ 系统道具发放, 在玩家登陆时到领奖中心获取奖励 """
    res_err = {'result': 1, \
               'errors': {'character_ids':'', 'items_list':[]}, \
               'success': {'character_ids':''}}

    if len(args) != 2:
        res_err['result'] = GM_INVALID_ARGS
        log.error('Args length error. args: {0}.'.format( args ))
        defer.returnValue( res_err )

    _character_cids = args['character_ids']
    _all_items      = args['item_lists']

    if not _character_cids:
        res_err['result'] = GM_INVALID_ARGS
        log.error('Unknown cids. _character_cids: {0}.'.format( _character_cids ))
        defer.returnValue( res_err )

    try:
        # 检查道具的类型和ID是否匹配
        _items_list = [[int(_item['item_type']), int(_item['item_id']), int(_item['item_cnt'])] for _item in _all_items]
        errorno, error_items = yield gs_call("gs_gm_check_grant_items", (_items_list, ))
        if errorno:
            res_err['result'] = GM_INVALID_ITEM
            res_err['errors']['items_list'] = error_items
            defer.returnValue( res_err )

        _grant_key  = int(time())
        # 处理玩家cid 列表
        _grant_cids   = [] # 需要在线发放item的玩家ID列表
        _connect_cids = g_UserMgr.connect_cids()
        if _character_cids == '-1':
            _character_cids = []
            _grant_cids = _connect_cids
        else:
            _character_cids = map(int, _character_cids.split(','))
            if not _character_cids or not isinstance(_character_cids, list):
                res_err['result'] = GM_INVALID_ARGS
                log.error('Unknown cids. _character_cids: {0}.'.format( _character_cids ))
                defer.returnValue(res_err)
            # 检查cid的合法性 未知cid将被忽略
            _invalid_cids = []
            for _cid in _character_cids:
                _valid_cid = yield redis.sismember(SET_CID_REGISTERED, _cid)
                if not _valid_cid:
                    _invalid_cids.append( _cid )
                    continue
                if _cid in _connect_cids:
                    _grant_cids.append( _cid )
            if _invalid_cids:
                res_err['result'] = GM_INVALID_CID
                res_err['errors']['character_ids'] = _invalid_cids
                defer.returnValue( res_err )

        # 在线玩家直接发送到领奖中心
        if _grant_cids:
            yield gs_call('gs_gm_grant_to_center', (_grant_cids, _grant_key, _items_list))

        # 保存发放记录
        _grant_info = marshal.dumps((_character_cids, _items_list, 0))
        yield redis.hset(HASH_GM_GRANT_ITEMS, _grant_key, _grant_info)
        # 更新返回值的信息
        if _character_cids != '-1':
            res_err['success']['character_ids'] = args['character_ids']

        defer.returnValue( res_err )
    except Exception as e:
        log.exception()
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue(res_err)

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_get_broadcast_msgs(cmd, ts, args, sign):
    ''' OSS获取当前的活动公告配置 '''

    res_err = {'result': 1, 'args': []}

    all_messages = curr_broadcast_messages()
    if all_messages is not None:
        for _id, _content in enumerate(all_messages):
            res_err['args'].append( {'id': _id+1, 'content': _content} )
        defer.returnValue( res_err )
    else:
        all_messages = []

    _all_msgs = yield redis.hget( HASH_OSS_MESSAGES, FIELD_BROADCAST )
    if not _all_msgs:
        defer.returnValue( res_err )
    else:
        _all_msgs = marshal.loads(_all_msgs)

    _args_data = []
    for _id, _content in enumerate(_all_msgs):
        _args_data.append( {'id': _id+1, 'content': _content} )
        all_messages.append( _content )

    if _args_data:
        res_err['args'] = _args_data
    # 更新内存数据
    sync_broadcast_messages( all_messages )

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_sync_broadcast_msgs(cmd, ts, args, sign):
    res_err = {'result': 1}

    msgs_data = {}
    for _msg in args:
        msgs_data[_msg['id']] = _msg['content']

    yield redis.delete( HASH_OSS_MESSAGES )
    if msgs_data:
        yield redis.hset( HASH_OSS_MESSAGES, FIELD_BROADCAST, marshal.dumps(msgs_data.values()) )

    # 更新内存数据
    sync_broadcast_messages( msgs_data.values() )

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_get_time_limited_shop_desc(cmd, ts, args, sign):
    ''' 查询限时商店说明配置 '''
    res_err = {'result': 1, 'args': {'title': '', 'content':''}}

    desc_msgs = yield redis.hget( HASH_OSS_MESSAGES, FIELD_LIMIT_SHOP_DESC )
    if not desc_msgs:
        defer.returnValue( res_err )
    else:
        desc_msgs = marshal.loads(desc_msgs)

    if isinstance(desc_msgs, dict):
        res_err['args'] = desc_msgs

    defer.returnValue( res_err )

@defer.inlineCallbacks
def gm_sync_time_limited_shop_desc(cmd, ts, args, sign):
    res_err = {'result': 1}
    if isinstance(args, dict):
        yield redis.hset( HASH_OSS_MESSAGES, FIELD_LIMIT_SHOP_DESC, marshal.dumps(args) )
    else:
        res_err['result'] = GM_INVALID_ARGS

    defer.returnValue( res_err )



INTERVAL_SECONDS = 0
LAST_TIME_GM_CMD = 0

gm_cmd_route = {
                   'add_credits': gm_add_credits, 
                     'add_items': gm_add_items,
          'online_realtime_data': gm_online_realtime_data,   # 在线实时数据
              'search_character': gm_search_character,       # 模糊玩家昵称搜索
                'character_info': gm_character_info,         # 玩家基本信息
                     'camp_info': gm_camp_info,              # 玩家的阵容信息
                      'bag_info': gm_bag_info,               # 玩家的背包信息
              'character_status': gm_character_status,       # 服务器上的封号/禁言玩家
                'character_mute': gm_character_mute,         # 对玩家禁言
           'character_forbidden': gm_character_forbidden,    # 对玩家封号
                'character_kick': gm_character_kick,         # 踢玩家下线
        'modify_character_level': gm_modify_character_level, # 修改玩家的等级
                'grant_items_to': gm_grant_items_to,         # 系统道具发放
            'get_broadcast_msgs': gm_get_broadcast_msgs,     # 查询走马灯的配置
           'sync_broadcast_msgs': gm_sync_broadcast_msgs,    # 同步走马灯的配置
    'get_time_limited_shop_desc': gm_get_time_limited_shop_desc,   # 查询限时商店说明配置
   'sync_time_limited_shop_desc': gm_sync_time_limited_shop_desc,  # 同步限时商店说明配置
    }

gs_gm_cmd_route = {
              'test_random_item': 2, # used for test
           'get_excite_activity': 2, # 查询精彩活动配置
          'sync_excite_activity': 2, # 同步精彩活动配置
              'get_limit_fellow': 2, # 查询限时神将配置
             'sync_limit_fellow': 2, # 同步限时神将配置
              'get_world_boss_duration': 2,       # 查询限时神将配置
             'sync_world_boss_duration': 2,       # 同步限时神将配置
  'get_time_limited_shop_item_duration': 2,       # 查询限时商店商品组开启时段配置
 'sync_time_limited_shop_item_duration': 2,       # 同步限时商店商品组开启时段配置
      'get_time_limited_shop_item_list': 2,       # 查询限时商店商品配置
     'sync_time_limited_shop_item_list': 2,       # 同步限时商店商品配置
                  'get_activity_notice': 2,       # 查询活动公告的配置
                 'sync_activity_notice': 2,       # 同步活动公告的配置
          #'get_activity_lottery_reward': 2,      # 查询活动翻牌奖励
          'sync_activity_lottery_reward': 2,      # 同步活动翻牌奖励
          #'get_active_monster_drop': 2,          # 查询活动怪物掉落
          'sync_activity_monster_drop': 2,        # 同步活动怪物掉落
          'sync_activity_random_package': 2,      # 同步随机礼包
          'get_pay_activity_group': 2,             # 查询累计充值分组配置
          'sync_pay_activity_group': 2,            # 同步累计充值分组配置
          'get_pay_activity_conf': 2,             # 查询累计充值详细配置
          'sync_pay_activity_conf': 2,            # 同步累计充值详细配置
          'get_consume_activity_group': 2,             # 查询累计消费分组配置
          'sync_consume_activity_group': 2,            # 同步累计消费分组配置
          'get_consume_activity_conf': 2,             # 查询累计消费详细配置
          'sync_consume_activity_conf': 2,            # 同步累计消费详细配置
}

@defer.inlineCallbacks
def gm_cmd(request):
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')

    # 检查上一次请求间隔, 防止被刷请求
    global LAST_TIME_GM_CMD
    res_err  = {'result': 1}
    req_args = request.args
    #log.error('For Test. last_time_gm_cmd: {0}, req_args: {1}.'.format( LAST_TIME_GM_CMD, req_args ))

    try:
        cmd  = request.args['cmd'][0]
        ts   = request.args['ts'][0]
        args = request.args['args'][0]
        sign = request.args['sign'][0]
    except Exception, e:
        log.error('Request error. e: {0}, req_args: {1}.'.format( e, req_args ))
        res_err['result'] = GM_INVALID_ARGS
        defer.returnValue( json.dumps(res_err) )
    ## 检查前后两条命令之间的请求间隔时间
    #if cmd not in ['camp_info']:
    #    if LAST_TIME_GM_CMD:
    #        if LAST_TIME_GM_CMD + INTERVAL_SECONDS > int(time()):
    #            res_err['result'] = GM_REQUEST_LIMIT
    #            defer.returnValue( json.dumps(res_err) )
    #    LAST_TIME_GM_CMD = int(time())

    #Check gm_sign
    sign_local = heitao_gm_sign(cmd, ts, args)
    if sign != sign_local:
        sign_local = base_gm_sign(cmd, ts, args)
        if sign != sign_local:
            log.error('Sign does not match! req {0}, local {1}'.format( sign, sign_local ))
            res_err['result'] = GM_INVALID_SIGN
            defer.returnValue( json.dumps(res_err) )

    try:
        args = json.loads(args)
        if gm_cmd_route.has_key(cmd):
            func = gm_cmd_route[cmd]
            res_data = yield func(cmd, ts, args, sign)
            #log.info('For Test. request cmd: {0}, res of data: {1}.'.format( cmd, res_data ))
        elif gs_gm_cmd_route.has_key(cmd):
            res_data = yield gs_call('gs_gm_%s'%cmd, (args, ))
        else:
            log.error('Invalid cmd : {0}.'.format( cmd ))
            res_err['result'] = GM_INVALID_CMD
            defer.returnValue( json.dumps(res_err) )

        defer.returnValue( json.dumps(res_data, cls=DecimalEncoder) )
    except Exception as e:
        log.error('Unknown error. e:{0}, req_args:{1}.'.format(e, req_args))
        log.exception()
        res_err['result'] = GM_INVALID_ERROR
        defer.returnValue( json.dumps(res_err) )


