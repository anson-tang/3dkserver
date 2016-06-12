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

from twisted.internet    import defer
from protocol_manager    import protocol_manager
from manager.csuser      import g_UserMgr
from manager.character   import Character


@route()
def registersrv(p, req):
    server = req
    p.setTimeout( None )
    protocol_manager.set_server(server, p)
    return (0, 0)

@route()
@defer.inlineCallbacks
def cs_character_login(p, req):
    res_err = [LOGIN_NO_CHARACTER, {}]
    cid,    = req

    character = Character(cid)
    try:
        load_data = yield character.load()
    except Exception as e:
        log.exception()
        defer.returnValue(res_err)

    if load_data:
        user = character.register()
        if user:
            defer.returnValue( [NO_ERROR, load_data] )
        else:
            log.error('Can not find user. cid: {0}, user: {1}.'.format( cid, user ))
            defer.returnValue( res_err )
    else:
        log.error('User no value. cid: {0}, load_data: {1}.'.format( cid, load_data ))
        defer.returnValue( res_err )

@route()
@defer.inlineCallbacks
def cs_new_character(p, req):
    _lead_id, _nick, _account, _sid = req

    res_err   = [REGISTER_FAIL_ERROR, []]
    character = Character()
    time_now  = int(time()) #datetime2string()
    try:
        new_value = yield character.new( need_load=False, account=_account, nick_name=_nick, sid=_sid, \
                lead_id=_lead_id, level=1, exp=0, vip_level=0, might=0, recharge=0, golds=0, credits=0, \
                credits_payed=0, total_cost=0, firstpay=0, monthly_card=0, dual_monthly_card=0, growth_plan=0, \
                register_time=time_now, last_login_time=time_now, fellow_capacity=BAG_DEFAULT_CAPACITY[3], \
                item_capacity=BAG_DEFAULT_CAPACITY[5], treasure_capacity=BAG_DEFAULT_CAPACITY[6], \
                equip_capacity=BAG_DEFAULT_CAPACITY[1], equipshard_capacity=BAG_DEFAULT_CAPACITY[2], \
                jade_capacity=BAG_DEFAULT_CAPACITY[7], soul=0, hunyu=0, prestige=0, honor=0, \
                energy=100, chaos_level=0, scene_star=0, douzhan=40, tutorial_steps='', \
                friends='', charge_ids='' )
    except Exception as e:
        log.error('New character error. e:{0}, req:{1}.'.format(e, req))
        defer.returnValue(res_err)

    user = character.register()
    if not user:
        log.error('Can not find user. cid: {0}, user: {1}.'.format( cid, user ))
        defer.returnValue( res_err )
    defer.returnValue( (NO_ERROR, new_value) )

@route()
def cs_character_logout(p, req):
    cid  = req
    user = g_UserMgr.getUser(cid)
    if user:
        user.last_hb_time = int(time())
        user.syncAllManagers()
        g_UserMgr.unregister(cid)
        return NO_ERROR
    else:
        return UNKNOWN_ERROR

@route()
@defer.inlineCallbacks
def cs_load_table_data(p, req):
    res_err    = [UNKNOWN_ERROR, {}]
    cid, table = req

    user       = g_UserMgr.getUser(cid)
    if not user:
        log.error('Can not find user. cid: {0}.'.format( cid ))
        defer.returnValue( res_err )

    cs_table_manager = user.getManager( table )
    if not cs_table_manager:
        log.warn('Can not find manager. table: {0}.'.format( table ))
        user.registerManager( table )
        cs_table_manager = user.getManager( table )
        if not cs_table_manager:
            log.error('Can not register manager. table: {0}.'.format( table ))
            defer.returnValue( res_err )

    try:
        table_data = yield cs_table_manager.load()
    except Exception as e:
        log.error('Exception raise. e: {0}'.format( e ))
        log.exception()
        defer.returnValue( res_err )

    defer.returnValue( (NO_ERROR, table_data) )

@route()
@defer.inlineCallbacks
def cs_new_attrib(p, req):
    '''
    @param  : kwargs format:{'id':*, 'cid':*, 'item_type':*, ...}
    @return : err, new_attrib_data
    '''
    res_err = [UNKNOWN_ERROR, None] 
    cid, table, need_load, kwargs = req

    user    = g_UserMgr.getUser(cid)
    if not user:
        log.warn('Can not find user. cid: {0}.'.format(cid))
        defer.returnValue( res_err )

    cs_table_manager = user.getManager( table )
    time_now         = int(time())
    if not cs_table_manager:
        log.error('Can not find manager. table: {0}.'.format( table ))
        user.registerManager( table )
        cs_table_manager = user.getManager( table )
        if not cs_table_manager:
            log.error('Can not register manager. table: {0}.'.format( table ))
            defer.returnValue( res_err )

    try:
        new_attrib_value = yield cs_table_manager.new( need_load=need_load, **kwargs )
    except Exception as e:
        log.warn('Exception raise. e: {0}.'.format( e ))
        log.exception()
        defer.returnValue( res_err )

    defer.returnValue( ( NO_ERROR, new_attrib_value ) )

@route()
@defer.inlineCallbacks
def cs_delete_attrib(p, req):
    res_err = UNKNOWN_ERROR
    cid, table, attrib_id = req

    user    = g_UserMgr.getUser(cid)
    if not user:
        log.warn('Can not find user. cid: {0}.'.format(cid))
        defer.returnValue(  )

    cs_table_manager = user.getManager( table )
    time_now         = int(time())
    if not cs_table_manager:
        log.error('Can not find manager. table: {0}.'.format( table ))
        user.registerManager( table )
        cs_table_manager = user.getManager( table )
        if not cs_table_manager:
            log.error('Can not register manager. table: {0}.'.format( table ))
            defer.returnValue( res_err )

    try:
        yield cs_table_manager.delete( attrib_id, None )
    except Exception as e:
        log.warn('Exception raise. e: {0}.'.format( e ))
        log.exception()
        defer.returnValue( res_err )

    defer.returnValue( NO_ERROR )

@route()
def cs_sync_user_attribute(p, req):
    #_data format: ( ( primary_key, where, dict_values ), ) 
    # 5951, 'character', ((xxxxx, None, {'golds':1222, ...}),)
    # 5951, 'fellow', ((123, None, {'golds':1222, ...}),(124, None, {'golds':1222, ...}),)
    #log.info('start, req:', req)
    #_cid, _table, _row_id, dirty_data = req
    dirty_attributes, = req

    for _cid, _table, _row_id, dirty_data in dirty_attributes:
        _user = g_UserMgr.getUser( _cid )
        if _user:
            _manager =_user.getManager( _table )
            if _manager:
                #log.info('User {0} update row id: {1}'.format( _cid, _row_id ))
                if _manager.isMultiRow():
                    update_data = [ (_row_id, None, dirty_data) ]
                    _manager.update( update_data )
                else:
                    _manager.update( dirty_data )
            else:
                log.warn('user\'s manager not found, cid:', _cid, _table, dirty_data)
        else:
            log.warn('User not found, cid:', _cid, _table, dirty_data)


