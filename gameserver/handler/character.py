#!/usr/bin/env python
#-*-coding: utf-8-*-

import random

from rpc        import route
from log        import log
from time       import time
from datetime   import datetime
from errorno    import *
from constant   import *
from redis      import redis
from marshal    import loads, dumps
from utils      import datetime2time, check_valid_time

from twisted.internet    import defer, reactor
from manager.gsuser      import g_UserMgr
from protocol_manager    import cs_call, ms_send, alli_call
from models.award_center import g_AwardCenterMgr
from models.worldboss    import worldBoss

from system              import get_version_conf, get_item_by_itemid
from syslogger           import syslogger



@route()
@defer.inlineCallbacks
def gs_login(p, req):
    res_err = [ UNKNOWN_ERROR, {}, [1, 1, 1, 1] ]
    cid, ver = req

    version_conf = get_version_conf()
    res_err[2]   = version_conf if version_conf else res_err[2]

    try:
        user_host = p.transport.getPeer().host
    except Exception, e:
        log.error(e)
        user_host = ''

    user = g_UserMgr.getUser(cid)
    if user:
        user.offline_flag = False
        char_data = user.base_att_value
        res_err   = [NO_ERROR, char_data, version_conf]
        yield check_grant_items(cid, user)
        log.warn('gameserver has user old data.')
        syslogger(LOG_LOGIN, cid, cid, user_host, ver, user.level, user.vip_level)
        defer.returnValue( res_err )

    try:
        res_err = yield cs_call("cs_character_login", [cid])
    except Exception as e:
        log.error('cs_character_login error. e: {0}'.format( e ))
        defer.returnValue( res_err )

    if res_err[0]:
        log.error('Get char data error. detail:', res_err)
        defer.returnValue( res_err )

    user = g_UserMgr.loginUser( res_err[1] )
    user.offline_flag = False
    yield check_grant_items(cid, user)
    syslogger(LOG_LOGIN, cid, cid, user_host, ver, user.level, user.vip_level)

    defer.returnValue( [NO_ERROR, user.base_att_value, version_conf] )

@defer.inlineCallbacks
def check_grant_items(cid, user):
    ''' 检查是否有全服发放的道具可领, 有时发放到领奖中心
    '''
    _register_ts    = datetime2time( user.base_att.register_time )
    _grant_keys_got = yield redis.smembers( SET_GOT_GRANT_KEYS%cid )

    _all_grants = yield redis.hgetall( HASH_GM_GRANT_ITEMS )
    if not _all_grants:
        defer.returnValue( NO_ERROR )

    for _grant_key, _grant_info in _all_grants.iteritems():
        _grant_key = int(_grant_key)
        # 判断注册时间点是否在发送道具时间点之后
        if _register_ts and _grant_key < _register_ts:
            continue
        if _grant_key in _grant_keys_got:
            continue
        # 检查时间是否过期, 14天
        if check_valid_time(_grant_key, hour=AWARD_VALID_HOURS):
            yield redis.hdel( HASH_GM_GRANT_ITEMS, _grant_key )
            continue
        # _grant_info=[玩家cid列表, 发放的道具, 过期时间戳]
        _grant_info = loads(_grant_info)
        if not _grant_info[0] or cid in _grant_info[0]:
            yield redis.sadd( SET_GOT_GRANT_KEYS%cid, _grant_key )
            yield g_AwardCenterMgr.new_award( cid, AWARD_TYPE_GM, [_grant_key, _grant_info[1]], flag=False )
 
    defer.returnValue( NO_ERROR )

@defer.inlineCallbacks
def gs_offline_login(cid):
    user = g_UserMgr.getUser(cid, True)
    if user:
        defer.returnValue( user )

    alliance_info = 0, '', 0
    try:
        res_err = yield cs_call("cs_character_login", [cid])
        # get alliance info
        alliance_info = yield alli_call('get_alliance_info', [cid])
    except Exception as e:
        log.error('cs_character_login error. e: {0}'.format( e ))
        defer.returnValue( None )

    if res_err[0]:
        log.error('Get char data error. cid: {0}, res_err: {1}.'.format(cid, res_err))
        defer.returnValue( None )

    user = g_UserMgr.loginUser( res_err[1], True )
    user.offline_flag = True
    if alliance_info[0] > 0:
        user.alliance_id = alliance_info[0]
        user.alliance_name = alliance_info[1]

    defer.returnValue( user )

@route()
@defer.inlineCallbacks
def gs_create_char(p, req):
    lead_id, nick_name, account, login_type, platform_id, version, sid = req

    res_err = [UNKNOWN_ERROR, None]

    try:
        res_err = yield cs_call("cs_new_character", (lead_id, nick_name, account, sid))
    except Exception as e:
        log.error('cs_new_character raise. e: {0}.'.format( e ))
        defer.returnValue(res_err)

    if res_err[0]:
        log.error('New char data error.')
        defer.returnValue( res_err )

    user = g_UserMgr.loginUser( res_err[1] )
    #yield user.sync_camp_to_redis()
    # new major fellow
    # args: fellow_id, is_major, camp_id, on_troop
    yield user.fellow_mgr.create_table_data( lead_id, 1, 1, FELLOW_FORMATION_ORDER[0]+1 )
    # a gift to new character
    yield user.fellow_mgr.create_table_data( 22071, 0, 0, 0 )
    yield user.bag_treasureshard_mgr.create_table_data( 12, 41001, 1, int(time()) )
    yield user.bag_treasureshard_mgr.create_table_data( 12, 41003, 1, int(time()) )
    try:
        device = login_type.split('/')
        if len(device) < 3:
            device = ['', '', '']
    except Exception, e:
        log.error(e)
        device = ['', '', '']

    try:
        user_host = p.transport.getPeer().host
    except Exception, e:
        log.error(e)
        user_host = ''

    syslogger(LOG_CHAR_NEW_1, user.cid, account, user.cid, user_host, device[0], device[1], device[2], nick_name, version, platform_id)

    defer.returnValue( [NO_ERROR, user.base_att_value] )

@route()
@defer.inlineCallbacks
def gs_logout(p, req):
    cid  = req
    user = g_UserMgr.getUser(cid)
    if not user:
        log.warn('User had logout. cid: {0}.'.format( cid ))
        defer.returnValue( UNKNOWN_ERROR )

    # 有离线登陆的玩家
    if user.offline_num > 0:
        log.warn('User had offline login, could not logout. cid: {0}.'.format( cid ))
        # 更新标志位为离线登陆标志
        user.offline_flag = True
        defer.returnValue( UNKNOWN_ERROR )

    if worldBoss.running:
        worldBoss.remove_attacker(cid)

    try:
        res = yield cs_call('cs_character_logout', cid)
    except:
        log.warn('Some exp raise in gs_logout. cid: {0}.'.format( cid ))
        defer.returnValue( UNKNOWN_ERROR )
    else:
        g_UserMgr.logoutUser(cid)
        log.debug('user logout sucess. cid: {0}.'.format( cid ))
        defer.returnValue( res )

@defer.inlineCallbacks
def gs_offline_logout(cid):
    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( UNKNOWN_ERROR )

    # 最后一个离线登陆时才做logou处理
    flag = user.logoutOffline()
    if not flag:
        defer.returnValue( UNKNOWN_ERROR )
    # 该玩家已正常登陆, 不做任何处理
    if not user.offline_flag:
        defer.returnValue( UNKNOWN_ERROR )

    try:
        res = yield cs_call('cs_character_logout', cid)
    except:
        log.error('Some exp raise in gs_logout') 
        defer.returnValue( UNKNOWN_ERROR )
    else:
        g_UserMgr.logoutUser(cid)
        log.debug('gs_offline_logout end. cid: ', cid)
        defer.returnValue( res ) 

@route()
@defer.inlineCallbacks
def gs_kickout_user(p, req):
    cid, = req
    user = g_UserMgr.getUser(cid)
    if not user:
        defer.returnValue( NO_ERROR )

    try:
        user.syncGameDataToCS()
        yield cs_call('cs_character_logout', cid)

        g_UserMgr.kickoutUser(cid)
    except:
        log.exception()
        defer.returnValue( UNKNOWN_ERROR )

@route()
def sync_user_to_cs(p, req):
    cid = req
    user = g_UserMgr.getUser(cid)
    if user:
        user.syncGameDataToCS()
        return NO_ERROR
    else:
        log.error('Can not find user, cid:', cid)
        return CONNECTION_LOSE

@route()
def skill_ball_unlock(p, req):
    cid, ball_index, unlock_type = req
    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid:', cid)
        return CONNECTION_LOSE, None
    res = user.skill_ball_unlock(int(ball_index), int(unlock_type))
    return res

@route()
@defer.inlineCallbacks
def get_player_camp(p, req):
    res_err = UNKNOWN_ERROR
    cid, [user_id] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )
    
    # 获取自己的阵容
    if user_id == cid:
        res_err = yield user.get_camp()
    else:
        offline_user = yield gs_offline_login( user_id )
        if offline_user:
            res_err = yield offline_user.get_camp(True)
            reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, user_id)

    if not res_err:
        log.error('No user camp data.')
        res_err = CHAR_DATA_ERROR

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def set_camp_one_touch(p, req):
    cid, [camp_id, one_touch_data] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.set_camp_one_touch(camp_id, one_touch_data)
    defer.returnValue( res_err )
 
@route()
@defer.inlineCallbacks
def set_camp_predestine(p, req):
    cid, [camp_pos_id, old_ufid, new_ufid] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.set_camp_predestine(camp_pos_id, old_ufid, new_ufid)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def decompose(p, req):
    ''' 炼化 '''
    cid, [_type, _user_ids] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.decompose(_type, _user_ids)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def batch_decompose(p, req):
    ''' 一键转化 '''
    cid, (_credits, ) = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.batch_decompose(_credits)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def reset_item(p, req):
    ''' 重生 '''
    cid, [_type, _user_id] = req
    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )


    res_err = yield user.reborn(_type, _user_id)
    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def payment_from_platfrom(p, req):
    res_err = [UNKNOWN_ERROR, 0]

    try:
        cid, orderno, charge_id, platform_id, parent_id, currency_type, currency = req
        user = g_UserMgr.getUser(cid)
        if user:
            old_credits = user.base_att.credits
            res_err[0], charge_type = yield user.add_credits(orderno, charge_id, platform_id, parent_id, currency_type, currency)
            _baseAttr  = user.base_att
            res_err[1] = (_baseAttr.credits - old_credits, _baseAttr.credits, _baseAttr.credits_payed, _baseAttr.vip_level, _baseAttr.monthly_card, charge_type)
        else:
            log.error('[ payment_from_platfrom ]can not find user. cid: {0}.'.format( cid ))
    except:
        log.exception('[ payment_from_platfrom ]req: {0}.'.format(req))

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def finished_dialogue_group(p, req):
    ''' 已完成的对话组 '''
    cid, = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield user.get_finished_group()

    defer.returnValue( res_err )
    
@route()
def finish_dialogue_group(p, req):
    ''' 请求完成某对话组 '''
    cid, [scene_id, group_id, dialogue_id] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    user.set_finished_group(scene_id, group_id, dialogue_id)

    return NO_ERROR

@route()
@defer.inlineCallbacks
def new_award_to_center(p, req):
    ''' 新增兑换码奖励到领奖中心 '''
    cid, item_id = req
 
    item_conf = get_item_by_itemid( item_id )
    if not item_conf:
        log.error('Can not find conf. cid: {0}, item_id: {1}.'.format( cid, item_id ))
        defer.returnValue( GIFT_CODE_OVERDUE )

    timestamp = int(time())
    yield g_AwardCenterMgr.new_award( cid, AWARD_TYPE_GIFT_CODE, [timestamp, [[item_conf['ItemType'], item_id, 1]]] )

    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def award_center_info(p, req):
    ''' 领奖中心列表 '''
    cid, = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_AwardCenterMgr.award_center_info( cid )

    defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def get_award_center(p, req):
    ''' 领取领奖中心的奖励 '''
    cid, [get_award_type, award_id] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    res_err = yield g_AwardCenterMgr.get_award_center( user, get_award_type, award_id )

    defer.returnValue( res_err )


@route()
def finish_tutorial(p, req):
    ''' 新手引导步骤完成 '''
    cid, (tutorial_step, ) = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    res_err = user.finish_tutorial( int( tutorial_step ) )

    return res_err

@route()
@defer.inlineCallbacks
def update_might(p, req):
    ''' 更新玩家的战斗力 '''
    cid, [new_might] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue(CONNECTION_LOSE)

    yield user.update_might( new_might )

    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def friend_list(p, req):
    ''' 获取好友列表 '''
    cid, [index] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    add_douzhan = yield user.goodwill_mgr.check_achieve()

    totals = len(user.friends)
    #成就
    yield user.achievement_mgr.update_achievement_status( ACHIEVEMENT_QUEST_ID_20, totals )
    friend_cids = user.friends[:index+20]
    if (not friend_cids):
        defer.returnValue( [index, totals, [], 0, GET_DOUZHAN_DAILY_LIMIT + add_douzhan] )
 
    # 给好友赠送斗战点的信息
    gift_cids = []
    gift_data = yield redis.hget(HASH_FRIENDS_SEND_DOUZHAN, cid)
    if gift_data:
        gift_data = loads(gift_data)
        dt_now    = datetime.now()
        dt_last   = datetime.fromtimestamp( gift_data[0] )
        if dt_last.date() == dt_now.date():
            gift_cids = gift_data[1]
 
    friend_info  = []
    offline_cids = []
    for _cid in friend_cids:
        online_user = g_UserMgr.getUser( _cid )
        if online_user:
            _info = online_user.friend_info()
            _info.append(1) # 0-离线, 1-在线
            _info.append( 1 if _cid in gift_cids else 0 ) # 0-未赠送, 1-已赠送
            # 在线好友排序 ??
            friend_info.append( _info )
        else:
            offline_cids.append( _cid )
 
    # 查询db 获取offline_cids的基本信息
    try:
        if offline_cids:
            dataset = yield cs_call("cs_offline_friends", [cid, offline_cids])
            if dataset:
                for _info in dataset:
                    _info = list( _info )
                    _info.append(0) # 0-离线, 1-在线
                    _info.append( 1 if _info[0] in gift_cids else 0 ) # 0-未赠送, 1-已赠送
                    friend_info.append( _info )
    except Exception as e:
        log.error('cs_offline_friends error. e: {0}'.format( e ))

    left_count, gift_data = yield get_friend_douzhan_status(cid, add_douzhan)

    defer.returnValue( [index, totals, friend_info, len(gift_data), left_count] )

@route()
@defer.inlineCallbacks
def friend_rand_list(p, req):
    ''' 随机玩家列表 '''
    cid, [nick_name] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if nick_name:
        # 搜索指定玩家
        try:
            _dataset = yield cs_call("cs_search_nick_name", [cid, nick_name])
            defer.returnValue( _dataset )
        except Exception as e:
            log.error('cs_search_nick_name error. e: {0}'.format( e ))
            defer.returnValue( [] )

    except_cids = user.friends
    except_cids.append( cid )
    # 随机的20为推荐玩家, 需要过滤掉自己和自己的好友
    rand_users = [] 
    users = g_UserMgr.getUserByLevel(user.level-5, user.level+5, except_cids)
    if len(users) >= FRIEND_RAND_MAX_COUNT:
        rand_users = random.sample(users, FRIEND_RAND_MAX_COUNT)
    else:
        users = g_UserMgr.getUserByLevel(user.level-10, user.level+10, except_cids)
        if len(users) >= FRIEND_RAND_MAX_COUNT:
            rand_users = random.sample(users, FRIEND_RAND_MAX_COUNT)
        else:
            users = g_UserMgr.getUserByLevel(0, 1000, except_cids)
            if len(users) >= FRIEND_RAND_MAX_COUNT:
                rand_users = random.sample(users, FRIEND_RAND_MAX_COUNT)
            else:
                rand_users = users

    rand_info = [_u.friend_info() for _u in rand_users]
    totals = len(rand_users)
    if totals >= FRIEND_RAND_MAX_COUNT:
        defer.returnValue( rand_info )

    # 查询db 获取离线玩家的基本信息
    try:
        for _u in rand_users:
            except_cids.append( _u.cid )
        offline_info = yield cs_call("cs_offline_rand_friends", [cid, FRIEND_RAND_MAX_COUNT-totals, user.level, except_cids])
        rand_info.extend( offline_info )
        defer.returnValue( rand_info )
    except Exception as e:
        log.error('cs_offline_rand_friends error. e: {0}'.format( e ))
        defer.returnValue( [] )

@route()
def friend_check_relation(p, req):
    ''' 查询两个玩家的好友关系 '''
    cid, [target_cid] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    if cid == target_cid:
        return USER_HAD_YOUR_FRIEND

    # 已经是好友了
    if target_cid in user.friends:
        log.error('Target user has been your friend. cid: {0}, target_cid:{1}.'.format( cid, target_cid ))
        return USER_HAD_YOUR_FRIEND

    return NO_ERROR

@route()
@defer.inlineCallbacks
def friend_invite(p, req):
    ''' 向玩家发送好友邀请 '''
    cid, [target_cid, content] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if cid == target_cid:
        defer.returnValue( USER_HAD_YOUR_FRIEND )

    # 已经是好友了
    if target_cid in user.friends:
        log.error('Target user has been your friend. cid: {0}, target_cid:{1}.'.format( cid, target_cid ))
        defer.returnValue( USER_HAD_YOUR_FRIEND )

    # 判断自己的好友人数
    if len(user.friends) >= MAX_FRIENDS_COUNT:
        log.error('User friends count has max. cid: {0}.'.format( cid ))
        defer.returnValue( FRIENDS_COUNT_SELF_ERROR )

    # 已经发送了好友邀请
    _key = HASH_MAIL_CONTENT % (MAIL_PAGE_FRIEND, target_cid)
    _all = yield redis.hgetall( _key )
    for _field, _value in _all.iteritems():
        if _field == MAIL_PRIMARY_INC:
            continue
        _value = loads(_value)
        if _value[3] != MAIL_FRIEND_1:
            continue
        if cid == _value[-1][0] and _value[-1][3] == 1:
            log.error('Target User has been invited. cid: {0}, target_cid: {1}.'.format( cid, target_cid ))
            defer.returnValue( INVITE_FRIEND_REPEAT )
    
    yield user.update_achievement_status(20, len(user.friends))
    # 发送邮件给target_cid
    ms_send('write_mail', (target_cid, MAIL_PAGE_FRIEND, MAIL_FRIEND_1, [cid, user.lead_id, user.nick_name, 1, content]))

    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def friend_discard(p, req):
    ''' 删除好友 '''
    cid, [target_cid] = req

    user = g_UserMgr.getUser( cid )
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    user.del_friends( target_cid )

    offline_user = yield gs_offline_login( target_cid )
    if offline_user:
        ms_send('write_mail', (target_cid, MAIL_PAGE_FRIEND, MAIL_FRIEND_6, [user.lead_id, user.nick_name]))

        offline_user.del_friends( cid )
        ms_send('write_mail', (cid, MAIL_PAGE_FRIEND, MAIL_FRIEND_5, [offline_user.lead_id, offline_user.nick_name]))
        reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, target_cid)

    # 删除双方互相赠送的斗战点
    yield redis.hdel( HASH_FRIENDS_GIFT_DOUZHAN % cid, target_cid )
    yield redis.hdel( HASH_FRIENDS_GIFT_DOUZHAN % target_cid, cid )

    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def handle_friend_invite(p, req):
    ''' 处理好友请求邮件 
    @param : status:2-同意, 3-拒绝;
    '''
    cid, [mail_id, status] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 更新原邮件状态 
    _key = HASH_MAIL_CONTENT % (MAIL_PAGE_FRIEND, cid)
    _value = yield redis.hget(_key, mail_id)
    if not _value:
        log.error('Unknown mail id. cid: {0}, mail_id: {1}, status: {2}.'.format( cid, mail_id, status ))
        defer.returnValue( UNKNOWN_MAIL_REQUEST )

    _value = loads(_value)
    if _value[2] != MAIL_PAGE_FRIEND or _value[3] != MAIL_FRIEND_1 or status not in [2, 3]:
        log.error('Unknown mail id. cid: {0}, mail_id: {1}, status: {2}.'.format( cid, mail_id, status ))
        defer.returnValue( UNKNOWN_MAIL_REQUEST )

    _value[-1][3] = status
    target_cid    = _value[-1][0]
    yield redis.hset(_key, mail_id, dumps(_value))

    # 同意时添加双方的friends列表. 发送新邮件
    if status == 2:
        # 判断自己的好友人数
        if len(user.friends) >= MAX_FRIENDS_COUNT:
            log.error('User friends count has max. cid: {0}.'.format( cid ))
            defer.returnValue( FRIENDS_COUNT_SELF_ERROR )

        # 处理对方
        offline_user = yield gs_offline_login( target_cid )
        if offline_user:
            reactor.callLater(SESSION_LOGOUT_REAL, gs_offline_logout, target_cid)
            # 判断对方好友人数限制
            if len(offline_user.friends) >= MAX_FRIENDS_COUNT:
                log.error('User friends count has max. target_cid: {0}.'.format( target_cid ))
                defer.returnValue( FRIENDS_COUNT_OTHER_ERROR )
            user.add_friends( target_cid )
            offline_user.add_friends( cid )
            ms_send('write_mail', (target_cid, MAIL_PAGE_FRIEND, MAIL_FRIEND_2, [user.lead_id, user.nick_name]))
    else:
        ms_send('write_mail', (target_cid, MAIL_PAGE_FRIEND, MAIL_FRIEND_3, [user.lead_id, user.nick_name]))

    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def friend_gift_douzhan(p, req):
    ''' 给好友赠送斗战点 '''
    cid, [rcv_cid] = req

    res_err = yield gift_douzhan(cid, rcv_cid)
    defer.returnValue( res_err )

@defer.inlineCallbacks
def gift_douzhan(send_cid, rcv_cid):
    user = g_UserMgr.getUser( send_cid )
    if not user:
        log.error('Can not find user. send_cid: {0}.'.format( send_cid ))
        defer.returnValue( CONNECTION_LOSE )

    # 维护自己的已赠送好友斗战点的信息
    send_data = yield redis.hget(HASH_FRIENDS_SEND_DOUZHAN, send_cid)
    if send_data:
        send_data = loads(send_data)
    else:
        send_data = [int(time()), []]

    dt_now    = datetime.now()
    dt_last   = datetime.fromtimestamp( send_data[0] )
    if dt_last.date() == dt_now.date():
        if rcv_cid in send_data[1]:
            #log.error('Rcv user had gift douzhan. send_cid: {0}, rcv_cid: {1}.'.format( send_cid, rcv_cid ))
            defer.returnValue( NO_ERROR )
        else:
            send_data[1].append( rcv_cid )
            yield redis.hset(HASH_FRIENDS_SEND_DOUZHAN, send_cid, dumps(send_data))
    else:
        send_data = [int(time()), [rcv_cid]]
        yield redis.hset(HASH_FRIENDS_SEND_DOUZHAN, send_cid, dumps(send_data))
 
    # 每日任务计数
    yield user.daily_quest_mgr.update_daily_quest( DAILY_QUEST_ID_10, 1 )
    # 维护好友的可领取斗战点的信息
    gift_data = dumps( (send_cid, user.lead_id, user.nick_name, user.level, user.might) )
    yield redis.hset( HASH_FRIENDS_GIFT_DOUZHAN % rcv_cid, send_cid, gift_data )

    defer.returnValue( NO_ERROR )

@route()
@defer.inlineCallbacks
def friend_douzhan_list(p, req):
    ''' 获取可领取斗战点的列表 '''
    cid, [index] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    add_douzhan = yield user.goodwill_mgr.check_achieve()

    left_count, gift_data = yield get_friend_douzhan_status(cid, add_douzhan)

    defer.returnValue( (index, len(gift_data), left_count, gift_data[index:index+20]) )

@defer.inlineCallbacks
def get_friend_douzhan_status(cid, add_douzhan=0):
    '''
    @param add_douzhan: 达成好感度成就后新增的领取斗战点次数
    '''
    left_count = GET_DOUZHAN_DAILY_LIMIT + add_douzhan
    gift_data  = []
    dt_now     = datetime.now()

    _all = yield redis.hgetall( HASH_FRIENDS_GIFT_DOUZHAN % cid )
    for _field, _value in _all.iteritems():
        if _field == FRIENDS_DOUZHAN_GET:
            last_time, left_count = loads(_value)
            dt_last = datetime.fromtimestamp( last_time )
            if dt_last.date() != dt_now.date():
                left_count = GET_DOUZHAN_DAILY_LIMIT + add_douzhan
                yield redis.hset( HASH_FRIENDS_GIFT_DOUZHAN % cid, FRIENDS_DOUZHAN_GET, dumps((int(time()), left_count)) )

        else:
            gift_data.append( loads(_value) )

    defer.returnValue( [left_count, gift_data] )


@route()
@defer.inlineCallbacks
def friend_get_douzhan(p, req):
    ''' 领取斗战点 '''
    cid, [send_cids] = req

    if not isinstance(send_cids, (list, tuple)):
        defer.returnValue( CLIENT_DATA_ERROR )

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( CONNECTION_LOSE )

    if user.douzhan >= 65535:
        log.error("User's douzhan had been max. cid: {0}.".format( cid ))
        defer.returnValue( DOUZHAN_MAX_ERROR )

    add_douzhan = yield user.goodwill_mgr.check_achieve()

    dt_now = datetime.now()
    _data  = yield redis.hget( HASH_FRIENDS_GIFT_DOUZHAN % cid, FRIENDS_DOUZHAN_GET )
    if _data:
        last_time, left_count = loads( _data )
        dt_last = datetime.fromtimestamp( last_time )
        if dt_last.date() != dt_now.date():
            left_count = GET_DOUZHAN_DAILY_LIMIT + add_douzhan
    else:
        left_count = GET_DOUZHAN_DAILY_LIMIT + add_douzhan

    if left_count < len(send_cids):
        log.error("User's gift douzhan count has used up today. left_count: {0}.".format( left_count ))
        defer.returnValue( DOUZHAN_DAILY_ERROR )

    for send_cid in send_cids:
        _data = yield redis.hget( HASH_FRIENDS_GIFT_DOUZHAN % cid, send_cid )
        if not _data:
            log.error('Can not find the gift douzhan. cid: {0}, send_cid: {1}.'.format( cid, send_cid ))
            continue
            #defer.returnValue( REQUEST_LIMIT_ERROR )

        yield redis.hdel( HASH_FRIENDS_GIFT_DOUZHAN % cid, send_cid )
        # 策划修改-好友赠送，每次改为2点
        user.add_douzhan( 2 )
        # 回赠
        yield gift_douzhan(cid, send_cid)
        # 更新今日可领次数
        left_count -= 1
        yield redis.hset( HASH_FRIENDS_GIFT_DOUZHAN % cid, FRIENDS_DOUZHAN_GET, dumps((int(time()), left_count)) )

    defer.returnValue( [user.douzhan] )

@route()
def friend_leave_msg(p, req):
    ''' 好友留言 '''
    cid, [rcv_cid, content] = req

    user = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        return CONNECTION_LOSE

    if rcv_cid not in user.friends:
        log.error('User has not in your friends list. cid: {0}, rcv_cid: {1}.'.format( cid, rcv_cid ))
        return USER_HAS_NOT_YOUR_FRIEND

    ms_send('write_mail', (rcv_cid, MAIL_PAGE_FRIEND, MAIL_FRIEND_4, [cid, user.lead_id, user.nick_name, content]))

    return NO_ERROR

@route()
@defer.inlineCallbacks
def get_resource_reward(p, req):
    ''' 领取第一次下载资源包的奖励 '''
    cid, [version] = req

    # 检查奖励是否已领取
    flag = yield redis.hexists(HASH_RESOURCE_REWARD, cid)
    if flag:
        log.error('Resource reward had got. cid: {0}.'.format( cid ))
        defer.returnValue( NO_ERROR )

    # 奖励发往领奖中心
    yield g_AwardCenterMgr.new_award( cid, AWARD_TYPE_RESOURCE_REWARD, [int(time())] )

    yield redis.hset(HASH_RESOURCE_REWARD, cid, version)

    defer.returnValue( NO_ERROR )


