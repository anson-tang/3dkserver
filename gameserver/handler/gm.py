#!/usr/bin/env python
#-*-coding: utf-8-*-

import MySQLdb

from rpc                 import route
from twisted.internet    import defer, reactor
from log                 import log
from errorno             import *
from constant            import *
from redis               import redis
from manager.gsuser      import g_UserMgr
from models.item         import *
from models.worldboss    import worldBoss
from protocol_manager    import cs_call, gw_broadcast
from handler.character   import gs_offline_logout
from models.award_center import g_AwardCenterMgr
from utils               import datetime2string, string2datetime, datetime2time, split_items

from system              import sysconfig, get_item_by_itemid, get_fellow_by_fid, check_item_id_and_type, check_excite_activity_status
from config              import sysconfig_db_conf

from manager.gslimit_fellow    import check_limit_fellow
from manager.gsexcite_activity import check_excite_activity
from models.timelimited_shop   import timeLimitedShop

from time import localtime, strftime, mktime, strptime

# 限时神将名列表
#FELLOW_NAMES = ['司马懿', '张辽', '赵云', '诸葛亮', '周瑜', '孙策', '左慈', '吕布', '大鹏金翅雕', '六耳猕猴', '如来佛祖', '孙悟空', '关羽', '阎罗', '玉帝', '于吉', '庞统']

@route()
@defer.inlineCallbacks
def gs_gm_login(p, req):
    ''' gm login gameserver as offline login 
    @param: query_flag-查询标志位 
    '''
    cid, query_flag = req

    user = g_UserMgr.getUser(cid, True)
    if user:
        defer.returnValue( NO_ERROR )

    try:
        res_err = yield cs_call("cs_character_login", [cid])
    except Exception as e:
        log.error('gm cs_character_login error. e: {0}'.format( e ))
        defer.returnValue( UNKNOWN_ERROR )

    if res_err[0]:
        log.error('Get char data error. cid: {0}, res_err: {1}.'.format(cid, res_err))
        defer.returnValue( res_err[0] )

    user = g_UserMgr.loginUser( res_err[1], flag=True )
    user.offline_flag = True
    yield user.fellow_mgr.value_list

    # 查询玩家离线登陆后 5min下线
    if query_flag:
        reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, cid)

    defer.returnValue( NO_ERROR )

@route()
def gs_gm_get_character_info(p, req):
    ''' return character info.
    '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Unknown user. cid: {0}.'.format( cid ))
        return {}
 
    _infos  = {}
    _fields = 'id', 'account', 'nick_name', 'lead_id', 'level', 'exp', \
            'vip_level', 'might', 'golds', 'credits', 'firstpay', 'monthly_card', \
            'register_time', 'last_login_time', 'soul', 'hunyu', 'prestige', 'energy', 'douzhan'
    for _key, _value in user.base_att.value.iteritems():
        if _key not in _fields:
            continue
        _infos[_key] = _value

    return _infos

@route()
@defer.inlineCallbacks
def gs_gm_get_camp_info(p, req):
    ''' return camp 1-6 detail info.
    '''
    cid, = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Unknown user. cid: {0}.'.format( cid ))
        defer.returnValue( [] )
 
    _camp_info   = []
    _camp_fellow = user.fellow_mgr.get_camp_fellow()
    for _idx, _ufid in enumerate( _camp_fellow ):
        _dict_data = {'camp_id':_idx+1, 'fellow':{}, 'helmet':{}, 
                'weapon':{}, 'necklace':{}, 'armor':{}, 
                'bookwar':{}, 'horse':{}}
        if _ufid <= 0:
            _camp_info.append( _dict_data )
            continue

        # 获取camp_id上的fellow
        _fellow = user.fellow_mgr.gm_get_camp_fellow( _ufid )
        if not _fellow:
            _camp_info.append( _dict_data )
            log.error('Unknown _ufid. cid: {0}, _ufid: {1}.'.format( cid, _ufid ))
            continue
        _dict_data['fellow'] = _fellow

        # 获取camp_id上的装备 2-头盔 3-武器, 4-项链, 5-护甲
        _dict_data['helmet'], _dict_data['weapon'], _dict_data['necklace'], _dict_data['armor'] = yield user.bag_equip_mgr.gm_get_camp_equip( _idx+1 )
        _dict_data['bookwar'], _dict_data['horse'] = yield user.bag_treasure_mgr.gm_get_camp_treasure( _idx+1 )
 
        _camp_info.append(_dict_data)

    defer.returnValue( _camp_info )

@route()
@defer.inlineCallbacks
def gs_gm_get_bag_info(p, req):
    ''' return bag info by type.
    param: bag_type 1-装备, 2-装备碎片, 3-伙伴背包, 4-分魂背包, 5-道具背包, 6-宝物背包, 7-战魂背包
    '''
    cid, bag_type = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Unknown user. cid: {0}.'.format( cid ))
        defer.returnValue( [] )

    _bag_info = []
    if bag_type == 1:
        _bag_info = yield user.bag_equip_mgr.gm_equip_info()
    elif bag_type == 2:
        _bag_info = yield user.bag_equipshard_mgr.gm_equipshard_info()
    elif bag_type == 3:
        _bag_info = yield user.fellow_mgr.gm_fellow_info()
    elif bag_type == 4:
        _bag_info = yield user.bag_fellowsoul_mgr.gm_fellowsoul_info()
    elif bag_type == 5:
        _bag_info = yield user.bag_item_mgr.gm_item_info()
    elif bag_type == 6:
        _bag_info = yield user.bag_treasure_mgr.gm_treasure_info()
    elif bag_type == 7:
        _bag_info = yield user.bag_treasureshard_mgr.gm_treasureshard_info()
    else:
        defer.returnValue( [] )

    defer.returnValue( _bag_info )

@route()
def gs_gm_modify_character_level(p, req):
    '''
    @return: [ status, level ]
    '''
    cid, target_level = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Unknown user. cid: {0}.'.format( cid ))
        return [ UNKNOWN_ERROR, 0 ] 

    if target_level > FELLOW_LEVELUP_LIMIT:
        target_level = FELLOW_LEVELUP_LIMIT

    last_level = user.base_att.level
    user.base_att.level = target_level
    log.debug('Character {0} level up, from {1} to {2}'.format( cid, last_level, user.base_att['level'] ))
    return [ 0 , user.base_att.level ]

@route()
def gs_gm_add_credits(p, req):
    '''
    @return: [ status, credits ]
    '''
    cid, add_credits = req
    
    user = g_UserMgr.getUser(cid)
    if not user:
        return [ UNKNOWN_ERROR, 0 ]

    last_credits = user.base_att['credits']
    user.base_att['credits'] += add_credits
    log.debug('Character {0} level up, from {1} to {2}'.format( cid, last_credits, user.base_att['credits'] ))
    return [ 0, user.base_att['credits'] ]

#ITEM_MODELS = {
#        ITEM_TYPE_ITEM: item_add_normal_item,
#        }

@route()
@defer.inlineCallbacks
def gs_gm_add_items(p, req):
    '''
    @return: [ status, quantity ]
    '''
    cid, item_type, item_id, add_count = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Unknown user. cid: {0}.'.format( cid ))
        defer.returnValue( [ UNKNOWN_ERROR, 0 ] )

    res_err = [UNKNOWN_ITEM_ERROR, 0]
    try:
        _model = ITEM_MODELs.get(item_type, None)
        if _model:
            res_err = yield _model(user, ItemID=item_id, ItemNum=add_count, AddType=WAY_GM_AWARD)
        else:
            defer.returnValue( res_err )
    except Exception as e:
        log.exception()
        log.error('Exception. e: {0}.'.format( e ))
        defer.returnValue( [ UNKNOWN_ERROR, 0 ] )

    defer.returnValue( res_err )
    
@route()
def gs_gm_check_grant_items(p, req):
    ''' 检查道具类型和道具ID是否匹配 '''
    items_list, = req
    error_items = []
    for _type, _id, _num in items_list:
        if _type == ITEM_TYPE_FELLOW:
            item_conf = get_fellow_by_fid( _id )
            if not item_conf:
                error_items.append( {'item_type':_type, 'item_id':_id} )
                continue
        else:
            item_conf = get_item_by_itemid( _id )
            if not item_conf or item_conf['ItemType'] != _type:
                error_items.append( {'item_type':_type, 'item_id':_id} )
                continue

    if error_items:
        return (UNKNOWN_ITEM_ERROR, error_items)
    else:
        return (NO_ERROR, error_items)

@route()
@defer.inlineCallbacks
def gs_gm_grant_to_center(p, req):
    ''' GM给在线玩家的奖励发放到领奖中心, '''
    all_cids, grant_key, items_list = req
 
    # 单次发放人数 100
    _loop_num = 100
    _tmp_cids = all_cids[:_loop_num]
    for cid in _tmp_cids:
        user = g_UserMgr.getUser(cid)
        if not user or user.offline_flag:
            continue

        yield redis.sadd( SET_GOT_GRANT_KEYS%cid, grant_key )
        yield g_AwardCenterMgr.new_award( cid, AWARD_TYPE_GM, [grant_key, items_list] )

    all_cids  = all_cids[_loop_num:]
    if all_cids:
        reactor.callLater(1, gs_gm_grant_to_center, all_cids, grant_key, items_list)
    else:
        defer.returnValue( NO_ERROR )

@route()
def gs_gm_get_excite_activity(p, req):
    ''' OSS获取当前的精彩活动配置 '''
    res_err = {'result': 1, 'args': []}

    _all_conf  = sysconfig.get('excite_activity', None)
    if not _all_conf:
        return _args_data

    _args_data = []
    for _conf in _all_conf.itervalues():
        if _conf['ActivityID'] not in [EXCITE_LIMIT_FELLOW, EXCITE_EXCHANGE_LIMITED, EXCITE_PAY_ACTIVITY, \
                EXCITE_CONSUME_ACTIVITY, EXCITE_PAY_CREDITS_BACK, EXCITE_NEWYEAR_PACKAGE, \
                EXCITE_HAPPY_NEW_YEAR, EXCITE_LOVER_KISS, EXCITE_DIG_TREASURE, EXCITE_GROUP_BUY, \
                EXCITE_LUCKY_TURNTABLE, EXCITE_ACTIVITY_NOTICE, EXCITE_TIME_LIMIT_SHOP]:
            continue
        _open_time  = datetime2string(_conf['OpenTime'])
        _close_time = datetime2string(_conf['CloseTime'])
        _dict_data = {'activity_id': _conf['ActivityID'], 'activity_name': _conf['ActivityName'], 'open_time':_open_time, 'close_time':_close_time}
        _args_data.append( _dict_data )

    if _args_data:
        res_err['args'] = _args_data
    return res_err

@route()
def gs_gm_sync_excite_activity(p, req):
    ''' OSS同步精彩活动配置, 并写database '''
    res_err = {'result': 1}

    all_new_conf, = req

    all_old_conf = sysconfig.get('excite_activity', None)
    if not all_old_conf:
        return res_err

    try:
        dataset  = {} # 被修改的活动配置
        for _new_conf in all_new_conf:
            _id = int(_new_conf['activity_id']) # 注意数据类型
            _old_conf = all_old_conf.get(_id, None)
            if not _old_conf:
                continue
            new_open_time = string2datetime(_new_conf['open_time'])
            new_close_time= string2datetime(_new_conf['close_time'])

            if _old_conf['OpenTime'] == new_open_time and _old_conf['CloseTime'] == new_close_time:
                continue

            _old_conf['OpenTime']  = new_open_time
            _old_conf['CloseTime'] = new_close_time
            # 获取被修改的活动信息
            dataset[_id] = [new_open_time, new_close_time, _id]

            all_old_conf[_id] = _old_conf
        # 没有修改
        if not dataset:
            log.info('Excite activity oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_EXCITE_ACTIVITY_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['excite_activity'] = all_old_conf

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()

    sql_update = 'UPDATE tb_excite_activity SET OpenTime=%s,CloseTime=%s WHERE ActivityID=%s;'

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    conn.close()

    # 重启精彩活动定时器
    for activity_id in dataset.keys():
        if activity_id == EXCITE_LIMIT_FELLOW:
            check_limit_fellow(deleted=True)
            continue
        check_excite_activity(activity_id, deleted=True)

    #if dataset.get(EXCITE_LIMIT_FELLOW, None):
    #    check_limit_fellow(deleted=True)
    #if dataset.get(EXCITE_PAY_ACTIVITY, None):
    #    check_excite_activity(EXCITE_PAY_ACTIVITY, deleted=True)
    #if dataset.get(EXCITE_CONSUME_ACTIVITY, None):
    #    check_excite_activity(EXCITE_CONSUME_ACTIVITY, deleted=True)
    #if dataset.get(EXCITE_PAY_CREDITS_BACK, None):
    #    check_excite_activity(EXCITE_PAY_CREDITS_BACK, deleted=True)

    return res_err

@route()
def gs_gm_get_limit_fellow(p, req):
    ''' OSS获取当前的限时神将活动配置 '''
    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('limit_fellow', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for _conf in _all_conf.itervalues():
        _dict_data  = {'activity_id': _conf['ActivityID'], 'fellow_name': _conf['ActivityName'], 'is_open':_conf['IsOpen']}
        _args_data.append( _dict_data )

    if _args_data:
        res_err['args'] = _args_data
    return res_err

@route()
def gs_gm_sync_limit_fellow(p, req):
    ''' OSS同步限时神将配置, 并写database '''
    res_err = {'result': 1}

    all_new_conf, = req

    all_old_conf = sysconfig.get('limit_fellow', None)
    if not all_old_conf:
        return res_err

    try:
        dataset    = {} # 被修改的限时神将配置
        _more_open = False # 是否有多个活动处于开启状态
        for _new_conf in all_new_conf:
            _id      = int(_new_conf['activity_id']) # 注意数据类型
            _is_open = int(_new_conf['is_open'])

            _old_conf = all_old_conf.get(_id, None)
            if not _old_conf:
                continue

            if _is_open:
                if _more_open:
                    res_err['result'] = OSS_LIMIT_FELLOW_ERROR
                    return res_err
                _more_open = True

            if _old_conf['IsOpen'] == _is_open:
                continue

            _old_conf['IsOpen'] = _is_open
            # 获取被修改的活动信息
            dataset[_id] = [_is_open, _id]

            all_old_conf[_id] = _old_conf
        # 没有修改
        if not dataset:
            log.info('Limit fellow oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_LIMIT_FELLOW_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['limit_fellow'] = all_old_conf

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()

    sql_update = 'UPDATE tb_limit_fellow SET IsOpen=%s WHERE ActivityID=%s;'

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    conn.close()

    # 重启限时神将定时器
    check_limit_fellow(deleted=True)

    return res_err

@route()
def gs_gm_get_world_boss_duration(p, req):
    ''' OSS获取当前的世界boss活动配置 '''
    _duration = worldBoss._duration

    res = [
            {'begin_hour':_duration[0][0], 'begin_min':_duration[0][1], 'begin_second':_duration[0][2]},
            {'end_hour':_duration[1][0], 'end_min':_duration[1][1], 'end_second':_duration[1][2]}
        ]

    return {'result': 1, 'args': res}

@route()
def gs_gm_sync_world_boss_duration(p, req):
    res_err = {'result': 10025}
    req = req[0]
    log.debug('req:', req)

    if len(req) == 2:
        try:
            _begin_conf, _end_conf = req[:]
            _b_hour, _b_min, _b_sec = map(int, (_begin_conf['begin_hour'], _begin_conf['begin_min'], _begin_conf['begin_second']))
            _e_hour, _e_min, _e_sec = map(int, (_end_conf['end_hour'], _end_conf['end_min'], _end_conf['end_second']))

            if _b_hour < 0 or _b_hour > 23 or _e_hour < 0 or _e_hour > 23:
                return res

            if _b_min < 0 or _b_min > 59 or _e_min < 0 or _e_min > 59:
                return res

            if _b_sec < 0 or _b_sec > 59 or _e_sec < 0 or _e_sec > 59:
                return res

            res_err['result'] = worldBoss.update_duration(((_b_hour, _b_min, _b_sec), (_e_hour, _e_min, _e_sec)))
        except:
            log.exception()
            res_err['result'] = 10025

    return res_err

def timestamp2str(seconds):
    return strftime('%Y-%m-%d %H:%M:%S', localtime(seconds))

@route()
def gs_gm_get_time_limited_shop_item_duration(p, req):
    ''' OSS获取当前的限时商店商品组开启时段配置 '''
    _groups = timeLimitedShop.groups_sorted

    res = {}
    for _group in _groups:
        res[str(_group.group_id)] = {'begin_time':timestamp2str(_group.begin_t), 'end_time':timestamp2str(_group.end_t)}

    return {'result': 1, 'args': res}

@route()
@defer.inlineCallbacks
def gs_gm_sync_time_limited_shop_item_duration(p, req):
    res_err = {'result': OSS_TIME_LIMITED_SHOP_GROUP_EXCEPTION}
    req = req[0]
    log.debug('req:', req)

    if req:
        try:
            res_err['result'] = yield timeLimitedShop.refresh_group_by_oss(req)
        except:
            log.exception()
            res_err['result'] = OSS_TIME_LIMITED_SHOP_GROUP_EXCEPTION

    defer.returnValue( res_err )

@route()
def gs_gm_get_time_limited_shop_item_list(p, req):
    ''' OSS获取当前的限时商店商品组开启时段配置 '''
    _items = timeLimitedShop.item_list()

    res = []
    for _item in _items:
        res.append(
                {
                    'GroupID':_item[0], 
                    'ID':_item[1], 
                    'ItemType':_item[2], 
                    'ItemID':_item[3], 
                    'Count':_item[4], 
                    'Information':_item[5], 
                    'OriginalPrice':_item[6], 
                    'CurrentPrice':_item[7], 
                    'LimitNum':_item[8]
                }
            )

    return {'result': 1, 'args': res}

@route()
def gs_gm_sync_time_limited_shop_item_list(p, req):
    res_err = {'result': OSS_TIME_LIMITED_SHOP_ITEM_EXCEPTION}
    req = req[0]
    log.debug('req:', req)

    if req:
        try:
            res_err['result'] = timeLimitedShop.refresh_item_by_oss(req)
        except:
            log.exception()
            res_err['result'] = OSS_TIME_LIMITED_SHOP_ITEM_EXCEPTION

    return res_err

@route()
def gs_gm_get_activity_notice(p, req):
    ''' OSS获取当前的活动公告配置 '''
    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('activity_notice', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for _c in _all_conf.itervalues():
        _args_data.append( {'id':_c['ID'], 
                         'title': _c['Title'], 
                       'content': _c['Content'], 
                     'open_time': datetime2string(_c['OpenTime']), 
                    'close_time': datetime2string(_c['CloseTime'])} )

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_activity_notice(p, req):
    ''' OSS同步活动公告配置, 并写database '''
    res_err = {'result': 1}

    all_new_conf, = req

    try:
        values = [] 
        all_old_conf = {} # 活动公告的配置
        for _new_conf in all_new_conf:
            _id = int(_new_conf['id']) # 注意数据类型
            all_old_conf[_id] = {}
            new_open_time = string2datetime(_new_conf['open_time'])
            new_close_time= string2datetime(_new_conf['close_time'])

            all_old_conf[_id]['ID'] = _id
            all_old_conf[_id]['Title']   = _new_conf['title']
            all_old_conf[_id]['Content'] = _new_conf['content']
            all_old_conf[_id]['OpenTime']  = new_open_time
            all_old_conf[_id]['CloseTime'] = new_close_time
            # 获取被修改的活动信息
            values.append( [_id, _new_conf['title'], _new_conf['content'], new_open_time, new_close_time] )

    except Exception as e:
        log.exception()
        res_err['result'] = OSS_ACTIVITY_NOTICE_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['activity_notice'] = all_old_conf
    # 通知在线玩家公告有变更
    gw_broadcast('sync_multicast', [SYNC_MULTICATE_TYPE_8, []])

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    cursor.execute( 'TRUNCATE TABLE tb_activity_notice;' )

    if values:
        sql_insert = 'INSERT INTO tb_activity_notice (ID,Title,Content,OpenTime,CloseTime) VALUES (%s,%s,%s,%s,%s);'
        cursor.executemany( sql_insert, values )

    conn.commit()

    cursor.close()
    conn.close()

    return res_err

@route()
def gs_gm_get_activity_lottery_reward(p, req):

    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('activity_lottery_oss', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for _c in _all_conf.itervalues():
        _args_data.append( {'id':_c['ID'], 
                         'vipLevel': _c['VipLevel'], 
                       'itemType': _c['ItemType'], 
                       'itemID': _c['ItemID'], 
                       'itemNum': _c['ItemNum'], 
                       'rate': _c['Rate'], 
                       'addRate': _c['AddRate'], 
                       'notice': _c['Notice'], 
                       'activeID': _c['ActiveID']
                       }) 

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_activity_lottery_reward(p, req):

    res_err = {'result': 1, 'error_id':0}
    all_new_conf, = req

    all_old_conf = {}
    try:
        dataset  = {} # 被修改的活动配置
        for _new_conf in all_new_conf:
            _id = int(_new_conf['id']) # 注意数据类型
            _old_conf = {}
            item_type, item_id = _new_conf['item_type'], _new_conf['item_id']
            _model = check_item_id_and_type(item_id, item_type)
            if not _model:
                res_err = {'result':OSS_ITEM_TYPE_IS_WRONG, 'error_id':_id}
                return res_err
            if int(_new_conf['activity_id']) <= 0:
                res_err = {'result': OSS_ACTIVITY_ID_WRONG, 'error_id':_id}
                return res_err
            _old_conf['RoleLevel']  = int(_new_conf['role_level'])
            _old_conf['VipLevel']  = int(_new_conf['vip_level'])
            _old_conf['ItemType']  = int(_new_conf['item_type'])
            _old_conf['ItemID']  = int(_new_conf['item_id'])
            _old_conf['ItemNum']  = int(_new_conf['item_num'])
            _old_conf['Rate']  = int(_new_conf['rate'])
            _old_conf['AddRate']= int(_new_conf['add_rate'])
            _old_conf['Notice'] = int(_new_conf['notice'])
            _old_conf['ActiveID']= int(_new_conf['activity_id'])
            # 获取被修改的活动信息
            dataset[_id] = [_id, _new_conf['role_level'], _new_conf['vip_level'], 
                            _new_conf['item_type'], _new_conf['item_id'], 
                            _new_conf['item_num'], _new_conf['rate'], 
                            _new_conf['add_rate'], _new_conf['notice'],
                            _new_conf['activity_id']]

            all_old_conf[_id] = _old_conf
        # 没有修改
        if not dataset:
            log.info('Activity lottery oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_ACTIVITY_LOTTERY_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['activity_lottery_oss'] = all_old_conf

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_activity_lottery_oss"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_activity_lottery_oss (ID, RoleLevel, VipLevel, ItemType, ItemID, ItemNum, Rate, AddRate, Notice, ActiveID) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    conn.close()

    return res_err

@route()
def gs_gm_get_active_monster_drop(p, req):

    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('monster_drop_oss', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for _c in _all_conf.itervalues():
        _args_data.append( {'dropID':_c['DropID'], 
                         'monsterID': _c['MonsterID'], 
                       'monsterDiff': _c['MonsterDiff'], 
                       'itemType': _c['ItemType'], 
                       'itemID': _c['ItemID'], 
                       'itemNum': _c['ItemNum'], 
                       'rateStart': _c['RateStart'], 
                       'rateAdd': _c['RateAdd'], 
                       'rateMax': _c['RateMax'], 
                       'activeID': _c['ActiveID']
                       }) 

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_activity_monster_drop(p, req):

    res_err = {'result': 1, 'error_id':0}
    all_new_conf, = req

    all_old_conf = {}

    try:
        dataset  = {} # 被修改的活动配置
        for _new_conf in all_new_conf:
            _id = int(_new_conf['id']) # 注意数据类型
            _old_conf = {}
            item_type, item_id = _new_conf['item_type'], _new_conf['item_id']
            _model = check_item_id_and_type(item_id, item_type)
            if not _model:
                res_err = {'result':OSS_ITEM_TYPE_IS_WRONG, 'error_id':_id}
                return res_err
            if int(_new_conf['activity_id']) <= 0:
                res_err = {'result': OSS_ACTIVITY_ID_WRONG, 'error_id':_id}
                return res_err
            _old_conf['MonsterID']  = int(_new_conf['monster_id'])
            _old_conf['MonsterDiff']  = int(_new_conf['monster_diff'])
            _old_conf['ItemType']  = int(_new_conf['item_type'])
            _old_conf['ItemID']  = int(_new_conf['item_id'])
            _old_conf['ItemNum']  = int(_new_conf['item_num'])
            _old_conf['RateStart']  = int(_new_conf['prob'])
            _old_conf['RateAdd']  = int(_new_conf['add_prob'])
            _old_conf['RateMax']  = int(_new_conf['max_prob'])
            _old_conf['ActiveID']  = int(_new_conf['activity_id'])
            # 获取被修改的活动信息
            dataset[_id] = [_id, _new_conf['monster_id'], _new_conf['monster_diff'], 
                            _new_conf['item_type'], _new_conf['item_id'], 
                            _new_conf['item_num'], _new_conf['prob'], 
                            _new_conf['add_prob'], _new_conf['max_prob'],
                            _new_conf['activity_id']]

            all_old_conf[_id] = _old_conf
        # 没有修改
        if not dataset:
            log.info('Active Monster Drop oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_ACTIVE_MONSTER_DROP_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['monster_drop_oss'] = all_old_conf

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_monster_drop_oss"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_monster_drop_oss (DropID, MonsterID, MonsterDiff, ItemType, ItemID, ItemNum, RateStart, RateAdd, RateMax, ActiveID) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    return res_err

@route()
def gs_gm_get_pay_activity_group(p, req):

    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('pay_activity_group', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for _c in _all_conf.itervalues():
        _args_data.append( {'group_id':_c['GroupID'], 
                            'group_desc': _c['GroupDesc'], 
                            'is_open': _c['IsOpen']
                       }) 

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_pay_activity_group(p, req):

    res_err = {'result': 1}
    all_new_conf, = req

    all_old_conf = {}
    
    try:
        if not check_excite_activity_status(EXCITE_PAY_ACTIVITY):
            return OSS_EXCITE_ACTIVITY_IS_CLOSED 
        dataset  = {} # 被修改的活动配置
        openList = []
        for _new_conf in all_new_conf:
            _old_conf = {}
            _old_conf['GroupID']  = int(_new_conf['group_id'])
            _old_conf['GroupDesc']  = _new_conf['group_desc']
            _old_conf['IsOpen']  = int(_new_conf['is_open'])
            # 获取被修改的活动信息
            dataset[_old_conf['GroupID']] = [_new_conf["group_id"], _new_conf['group_desc'], _new_conf['is_open']] 
            all_old_conf[_old_conf["GroupID"]] = _old_conf
            if int(_new_conf['is_open']):  
                openList.append(_new_conf['is_open'])
        # 没有修改
        if openList.count(1) > 1 or len(openList) == 0:
            res_err = {'result': OSS_ACTIVITY_GROUP_OPEN_WRONG}
            return res_err
        if not dataset:
            log.info('Pay activity group oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_PAY_ACTIVITY_GROUP_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['pay_activity_group'] = all_old_conf
    #gw_broadcast('sync_multicast', [SYNC_MULTICATE_TYPE_9, []])

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_pay_activity_group"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_pay_activity_group (GroupID, GroupDesc, IsOpen) VALUES(%s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    return res_err

@route()
def gs_gm_sync_activity_random_package(p, req):

    res_err = {'result': 1, 'error_id' : 0}
    all_new_conf, = req

    all_old_conf = {}

    try:
        dataset  = {} # 被修改的活动配置
        for _new_conf in all_new_conf:
            _package_id   = int(_new_conf['package_id'])
            _package_type = int(_new_conf['package_type'])
            _old_conf = all_old_conf.setdefault(_package_id, [[],[],[]])
            _id = int(_new_conf['id']) # 注意数据类型
            item_type, item_id = _new_conf['item_type'], _new_conf['item_id']
            _model = check_item_id_and_type(item_id, item_type)
            if not _model:
                res_err = {'result':OSS_ITEM_TYPE_IS_WRONG, 'error_id':_id}
                return res_err
            if int(_new_conf['activity_id']) <= 0:
                res_err = {'result': OSS_ACTIVITY_ID_WRONG, 'error_id':_id}
                return res_err
            if _package_type > 2:
                res_err = {'result': OSS_PACKAGE_TYPE_ERROR, 'error_id':_id}
                return res_err
            _conf = {}
            _conf['PackageID']   = _package_id
            _conf['PackageType'] = _package_type
            _conf['RoleLevel']   = int(_new_conf['role_level'])
            _conf['VipLevel']    = int(_new_conf['vip_level'])
            _conf['ItemType']    = int(_new_conf['item_type'])
            _conf['ItemID']      = int(_new_conf['item_id'])
            _conf['ItemNum']     = int(_new_conf['item_num'])
            _conf['Rate']        = int(_new_conf['prob'])
            _conf['Notice']      = int(_new_conf['notice'])
            _conf['ActivityID']  = int(_new_conf['activity_id'])
            # 获取被修改的活动信息
            dataset[_id] = [_package_id, _package_type, _new_conf['role_level'], _new_conf['vip_level'], _new_conf['item_type'], _new_conf['item_id'], _new_conf['item_num'], _new_conf['prob'], _new_conf['notice'], _new_conf['activity_id']] 
            _old_conf[_package_type].append( _conf )
        # 没有修改
        if not dataset:
            log.info('Random package oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_ACTIVITY_RANDOM_PACKAGE_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['package_oss'] = all_old_conf

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_package_oss"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_package_oss (PackageID, PackageType, RoleLevel, VipLevel, ItemType, ItemID, ItemNum, Rate, Notice, ActivityID) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    return res_err
@route()
def gs_gm_get_pay_activity_conf(p, req):

    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('pay_activity_oss', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for groupID, _conf in _all_conf.iteritems():
        for _, _c in _conf.iteritems():
            award = ""
            for a, b, c in _c['AwardList']:
                award += ",%s:%s:%s" % (str(a), str(b), str(c))
            award = award.replace(",","",1)
            _args_data.append( {'id':_c['ID'],
                            'group_id':groupID, 
                            'pay': _c['TotalPay'], 
                            'award_list': award
                       }) 

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_pay_activity_conf(p, req):

    res_err = {'result': 1, 'error_id':0}
    all_new_conf, = req

    all_old_conf = {}

    try:
        dataset  = {} # 被修改的活动配置
        for _new_conf in all_new_conf:
            _id = int(_new_conf['id']) # 注意数据类型
            _old_conf = {}
            _old_conf['ID'] = int(_id)
            _old_conf['GroupID']  = int(_new_conf['group_id'])
            _old_conf['TotalPay']  = int(_new_conf['pay'])
            _old_conf['AwardList'] = split_items(_new_conf['award_list'])
            for item_type, item_id, add_count in _old_conf['AwardList']:
                _model = check_item_id_and_type(item_id, item_type)
                if not _model:
                    res_err = {'result':OSS_ITEM_TYPE_IS_WRONG, 'error_id':_id}
                    return res_err
            # 获取被修改的活动信息
            dataset[_id] = [_new_conf["group_id"], _new_conf['pay'], _new_conf['award_list']] 
            if not all_old_conf.has_key(int(_new_conf['group_id'])):
                all_old_conf[int(_new_conf['group_id'])] = {}
            all_old_conf[int(_new_conf['group_id'])][_id] = _old_conf
        # 没有修改
        if not dataset:
            log.info('Pay activity conf oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_PAY_ACTIVITY_CONF_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['pay_activity_oss'] = all_old_conf

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_pay_activity_oss"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_pay_activity_oss (GroupID, TotalPay, AwardList) VALUES(%s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    return res_err

@route()
def gs_gm_get_consume_activity_group(p, req):

    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('consume_activity_group', None)
    if not _all_conf:
        return res_err

    _args_data = []
    for _c in _all_conf.itervalues():
        _args_data.append( {'group_id':_c['GroupID'], 
                            'group_desc': _c['GroupDesc'], 
                            'is_open': _c['IsOpen']
                       }) 

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_consume_activity_group(p, req):

    res_err = {'result': 1}
    all_new_conf, = req

    all_old_conf = {}

    try:
        if not check_excite_activity_status(EXCITE_CONSUME_ACTIVITY):
            return OSS_EXCITE_ACTIVITY_IS_CLOSED 
        dataset  = {} # 被修改的活动配置
        openList = [] # 检查打开组
        for _new_conf in all_new_conf:
            _old_conf = {}
            _old_conf['GroupID']  = int(_new_conf['group_id'])
            _old_conf['GroupDesc']  = _new_conf['group_desc']
            _old_conf['IsOpen']  = int(_new_conf['is_open'])
            # 获取被修改的活动信息
            dataset[_old_conf['GroupID']] = [_new_conf["group_id"], _new_conf['group_desc'], _new_conf['is_open']] 
            all_old_conf[_old_conf["GroupID"]] = _old_conf
            if _new_conf['is_open']:
                openList.append(_new_conf['is_open'])
        # 没有修改
        if openList.count(1) > 1 or len(openList) == 0:
            res_err = {'result': OSS_ACTIVITY_GROUP_OPEN_WRONG}
            return res_err
        if not dataset:
            log.info('Consume activity group oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_CONSUME_ACTIVITY_GROUP_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['consume_activity_group'] = all_old_conf
    #gw_broadcast('sync_multicast', [SYNC_MULTICATE_TYPE_10, []])

    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_consume_activity_group"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_consume_activity_group (GroupID, GroupDesc, IsOpen) VALUES(%s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    return res_err


@route()
def gs_gm_get_consume_activity_conf(p, req):

    res_err = {'result': 1, 'args': []}

    _all_conf = sysconfig.get('consume_activity_oss', None)
    if not _all_conf:
        return res_err

    _args_data = []

    for groupID, _conf in _all_conf.iteritems():
        for _, _c in _conf.iteritems():
            award = ""
            for a, b, c in _c['AwardList']:
                award += ",%s:%s:%s" % (str(a), str(b), str(c))
            award = award.replace(",","",1)
            _args_data.append( {'id':_c['ID'],
                            'group_id':groupID, 
                            'consume': _c['TotalConsume'], 
                            'award_list': award
                       }) 

    if _args_data:
        res_err['args'] = _args_data

    return res_err

@route()
def gs_gm_sync_consume_activity_conf(p, req):

    res_err = {'result': 1, 'error_id':0}
    all_new_conf, = req

    all_old_conf = {}

    try:
        dataset  = {} # 被修改的活动配置
        for _new_conf in all_new_conf:
            _id = int(_new_conf['id']) # 注意数据类型
            _old_conf = {}
            _old_conf['ID'] = _id
            _old_conf['GroupID'] = _new_conf['group_id']
            _old_conf['TotalConsume'] = _new_conf['consume']
            _old_conf['AwardList'] = split_items(_new_conf['award_list'])
            for item_type, item_id, add_count in _old_conf['AwardList']:
                _model = check_item_id_and_type(item_id, item_type)
                if not _model:
                    res_err = {'result':OSS_ITEM_TYPE_IS_WRONG, 'error_id':_id}
                    return res_err
            # 获取被修改的活动信息
            dataset[_id] = [_new_conf["group_id"], _new_conf['consume'], _new_conf['award_list']]
            if not all_old_conf.has_key(int(_new_conf['group_id'])):
                all_old_conf[int(_new_conf['group_id'])] = {}
            all_old_conf[int(_new_conf['group_id'])][_id] = _old_conf

        # 没有修改
        if not dataset:
            log.info('Consume activity conf oss conf no changed.')
            return res_err
    except Exception as e:
        log.exception()
        res_err['result'] = OSS_CONSUME_ACTIVITY_CONF_ERROR
        return res_err

    # 更新内存中的 sysconfig
    sysconfig['consume_activity_oss'] = all_old_conf
    # 更新db
    conn   = MySQLdb.connect(**sysconfig_db_conf)
    cursor = conn.cursor()
    sql_delete = "TRUNCATE table tb_consume_activity_oss"
    cursor.execute(sql_delete)
    conn.commit()
    sql_update = "INSERT INTO tb_consume_activity_oss (GroupID, TotalConsume, AwardList) VALUES(%s, %s, %s)"

    cursor.executemany( sql_update, dataset.values() )
    conn.commit()

    cursor.close()
    return res_err
