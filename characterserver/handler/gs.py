#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from rpc      import route
#from log      import log
#from errorno  import *
#from constant import *
#from time     import time
#from utils    import datetime2string
#
#from twisted.internet import defer
#from protocol_manager import protocol_manager,gs_call
#
##from manager.cscharacter import CSCharacter
##from manager.csfellow    import CSFellowMgr
#from manager.csuser      import g_UserMgr, CSUser
#from manager.character   import Character
#from manager.fellow      import CSFellowMgr
#from manager.bag         import BagNormal
#
#@route()
#def registersrv(p, req):
#    server = req
#    protocol_manager.set_server(server, p)
#    return (0, 0)
#
#@route()
#@defer.inlineCallbacks
#def cs_login(p, req):
#    '''
#    @return: ( errno, char_data {fn:value, ... }, fellow_data { ufid:{ fn:v, ... }, ... }, bag_normal_data { uiid:{ fn:v, ... }, ... )
#    '''
#    cid = req
#    #ch = None #ch = CSCharacter( { 'account' : account }, False )
#
#    res_err = [LOGIN_NO_CHARACTER, {}, {}]
#    dic_id_row = {}
#    character = Character(cid)
#    user = None
#    try:
#        load_res = yield character.load()
#    except Exception as e:
#        log.exception()
#        defer.returnValue(res_err)
#
#    #log.debug('Character::load() return :', load_res)
#    _char_value = character.value
#    if len(_char_value) > 0:
#        user = character.register()
#        if user:
#            fellow_data=None
#            bag_data = None
#            try:
#                errno, fellow_data = yield user.load_aux_data()
#                #errno, fellow_data, bag_normal_data = yield user.load_aux_data()
#            except Exception as e:
#                log.warn('Exp raise in CSUser::load_aux_data(), e:', e)
#                defer.returnValue(res_err)
#            else:
#                fellow = user.getManager(Fellow._table)
#
#                if fellow:
#                    if len(fellow.value) == 0:
#                        yield cs_create_major_fellow(user.cid, fellow)
#                        fellow_data = fellow.value
#                        log.debug('Create major fellow. cid:', user.cid)
#                else:
#                    log.error('Exp398372 fellow is none! cid:', user.cid)
#
#                defer.returnValue( (0, character.new_value(), fellow_data) )
#                #defer.returnValue( (0, character.value, fellow_data, bag_normal_data ) )
#        else:
#            log.error('Can not find user. cid: {0}, user: {1}.'.format( cid, user ))
#            defer.returnValue( res_err )
#    else:
#        log.error('User no value. cid: {0}, char_value: {1}.'.format( _char_value ))
#        defer.returnValue( res_err )
#
#@route()
#@defer.inlineCallbacks
#def cs_create_character(p, req):#Return: errno, char_data {}, fellow_data {}
#    _lead_id, _nick, _account = req
#
#    res_err   = [UNKNOWN_ERROR, {}, {}]
#    character = Character()
#    time_now  = datetime2string()
#    user = None
#    try:
#        #yield character.new( account=_account, nick_name=_nick, lead_id=_lead_id, level=1, exp=0, vip_level=0, might=0, recharge=0, golds=0, credits=0, credits_payed=0, register_time=time_now, fellow_capacity=BAG_DEFAULT_CAPACITY[3], item_capacity=BAG_DEFAULT_CAPACITY[5], treasure_capacity=BAG_DEFAULT_CAPACITY[6], equip_capacity=BAG_DEFAULT_CAPACITY[1], equipshard_capacity=BAG_DEFAULT_CAPACITY[2], soul=CHARACTER_DEFAULT_SOUL, hunyu=0, prestige=0, energy=CHARACTER_DEFAULT_ENERGY, chaos_level=0 )
#        yield character.new( need_load=False, account=_account, nick_name=_nick, lead_id=_lead_id, level=1, exp=0, vip_level=0, might=0, recharge=0, golds=1000000000, credits=1000000000,
#                credits_payed=0, register_time=time_now, fellow_capacity=BAG_DEFAULT_CAPACITY[3], item_capacity=BAG_DEFAULT_CAPACITY[5], treasure_capacity=BAG_DEFAULT_CAPACITY[6],
#                equip_capacity=BAG_DEFAULT_CAPACITY[1], equipshard_capacity=BAG_DEFAULT_CAPACITY[2], soul=CHARACTER_DEFAULT_SOUL, hunyu=0, prestige=0, energy=20, chaos_level=0, scene_star=0, douzhan=20 )
#    except Exception as e:
#        log.debug('Exp raise in Character::new. e:', e)
#        defer.returnValue(res_err)
#
#    new_cid = character.dict_attribs._Attribute__uid
#    log.debug('Character::new ok. new_cid:', new_cid)
#
#    try:
#        yield character.load( True, { 'id' : new_cid } )
#    except Exception as e:
#        log.debug('Exp raise in Character::load(). e:', e)
#        log.exception()
#        defer.returnValue(res_err)
#
#    user = character.register()
#    ch = user.getManager(Character._table)
#
#    err, fellow = user.create_aux_data(new_cid)
#    #err, fellow, bag_normal = user.create_aux_data(new_cid)
#
#    try:
#        yield cs_create_major_fellow(new_cid, fellow)
#    except Exception as e:
#        log.debug('Exp93877 raise. e:', e)
#        log.exception()
#        defer.returnValue(res_err)
#
#    log.info('Create character ok. ch-data:', character.value, ' fellow-data:', fellow.value)
#    defer.returnValue( (NO_ERROR, character.value, fellow.value) )
#    #defer.returnValue( (NO_ERROR, character.value, fellow.value, bag_normal.value) )
#
#@defer.inlineCallbacks
#def cs_create_major_fellow(cid, fellow):
#    log.debug('cs create major fellow start. cid:', cid)
#    res_err = (UNKNOWN_ERROR, [])
#    
#    user = g_UserMgr.getUser(cid)
#    if not user:
#        log.warn('Exp3987761 Can not find user:',cid) 
#        defer.returnValue( res_err )
#
#    fid = 21001 #Optimize later, need special value for major fellow
#    attr_value = {}
#
#    character = user.getManager('character')
#    if not character:
#        log.warn('Exp3989383 Can not find attribute of character. cid:', cid)
#        defer.returnValue( res_err )
#
#    time_now  = datetime2string()
#    char_data = character.value
#    #log.debug('Data of character:', char_data)
#    #.. Finish it later, we will get major's 'exp' and 'QualityLevel' from tb_character
#    exp_major = 0
#    ql_major = 1
#
#    try:
#        if 0 != fid:
#            attr_value = yield fellow.new( cid=cid, fellow_id = fid, level=1, \
#                exp=exp_major, advanced_level=ql_major, on_troop=FELLOW_FORMATION_ORDER[0]+1, \
#                is_major = True, camp_id=1, deleted=0, create_time=time_now, update_time=time_now, del_time=0 )
#    except Exception as e:
#        log.warn('Exp raise in Fellow::new. e:', e)
#        log.exception()
#        defer.returnValue( res_err )
#    else:
#        log.debug('Fellow::new return ', attr_value)
#
#    #ufid = attr_value['id']
#    #try:
#    #    yield fellow.load( True, { 'id' : ufid } )#There's only one row here. So you can over write it.
#    #except Exception as e:
#    #    log.warn('Exp raise in Fellow::new. e:', e)
#    #    log.exception()
#    #    defer.returnValue( res_err )
#
#    log.debug('cs create major fellow end. Fellows:', fellow.value)
#    defer.returnValue( 0 )
#
#@route()
#def cs_logout(p, req):
#    cid = req
#    user = g_UserMgr.getUser(cid)
#    if user:
#        user.last_hb_time = int(time())
#        user.syncAllManagers()
#        g_UserMgr.unregister(cid)
#        return 0
#    else:
#        return UNKNOWN_ERROR
#
#
#@route()
#@defer.inlineCallbacks
#def cs_create_item(p, req):#Return : err, new_item_data
#    log.debug('cs_create_item start. req:', req)
#    cid, item_type, item_id, count = req
#
#    user = g_UserMgr.getUser(cid)
#    if not user:
#        log.warn('Exp3987751 Can not find user:',cid) 
#        defer.returnValue( ( UNKNOWN_ERROR, None ) )
#
#    bag_normal = user.getManager(BagNormal._table)
#    time_now = int(time())
#    try:
#        new_item_value = yield bag_normal.new( cid=cid, item_type=item_type, item_id=item_id, count=count, deleted=0, \
#            create_time=time_now, update_time=time_now, del_time=0)
#    except Exception as e:
#            log.warn('Exp raise in Fellow::new. e:', e)
#            log.exception()
#            defer.returnValue( ( UNKNOWN_ERROR, None ) )
#
#    log.debug('[ cs_create_item ] end, new item:', new_item_value)
#    defer.returnValue( ( 0, new_item_value ) )
#
#@route()
#@defer.inlineCallbacks
#def cs_create_fellow(p, req):#Return:  errno, { ufid:fellow_data, ... }
#    cid, fellow_id_list = req
#    log.debug('cs_create_fellow start. req:', req)
#
#    res_err = (UNKNOWN_ERROR, {})
#    
#    user = g_UserMgr.getUser(cid)
#    if not user:
#        log.warn('Exp3987762 Can not find user:',cid) 
#        defer.returnValue( res_err )
#
#    fellow = user.getManager(CSFellowMgr._table)
#    if None == fellow:
#        defer.returnValue( res_err )
#
#    time_now   = datetime2string()
#    list_new_fellow = []
#    for fid in fellow_id_list:
#        attr_value = {}
#        try:
#            if 0 != fid:
#                attr_value = yield fellow.new(cid=cid, fellow_id = fid, level=FELLOW_DEFAULT_LEVEL, \
#                    exp=FELLOW_DEFAULT_EXP, advanced_level=FELLOW_DEFAULT_QUALITY_LEVEL, on_troop=0, \
#                    is_major=False, camp_id=0, deleted=0, create_time=time_now, update_time=time_now, del_time=0 )
#        except Exception as e:
#            log.warn('Exp raise in Fellow::new. e:', e)
#            log.exception()
#            defer.returnValue( res_err )
#        else:
#            list_new_fellow.append( attr_value )
#        #log.debug('Fellow::new return ', attr_value)
#
#    log.debug('cs_create_fellow end. new fellow count: ', len(list_new_fellow))
#    defer.returnValue( ( 0, list_new_fellow) )
#
#
#@route()
#def cs_del_user_attribute(p, req):
#    log.debug('[ cs_del_user_attribute ] start, req:', req)
#    _cid, _table, _row_id = req
#
#    _user = g_UserMgr.getUser( _cid )
#    if _user:
#        _manager =_user.getManager( _table )
#        if _manager:
#            _manager.delete( _row_id, None )
#            log.warn('[ cs_del_user_attribute ] end :user , cid:', _cid, '  delete row:', _row_id)
#        else:
#            log.warn('[ cs_del_user_attribute ] fail :user\'s manager not found, cid:', _cid, _table)
#    else:
#        log.warn('[ cs_del_user_attribute ] fail :user not found, cid:', _cid, _table)
#
#@route()
#def cs_sync_user_attribute(p, req):
#    #_data format: ( ( primary_key, where, dict_values ), ) 
#    # 5951, 'character', ((xxxxx, None, {'golds':1222, ...}),)
#    # 5951, 'fellow', ((123, None, {'golds':1222, ...}),(124, None, {'golds':1222, ...}),)
#    log.debug('[ cs_sync_user_attribute ] start, req:', req)
#    _cid, _table, _row_id, dirty_data = req
#
#    _user = g_UserMgr.getUser( _cid )
#    if _user:
#        _manager =_user.getManager( _table )
#        if _manager:
#            log.debug('[ cs_sync_user_attribute ] user {0} update row {1}'.format( _cid, _row_id ))
#            if _manager.isMultiRow():
#                update_data = [ (_row_id, None, dirty_data) ]
#                _manager.update( update_data )
#            else:
#                _manager.update( dirty_data )
#        else:
#            log.warn('[ cs_sync_user_attribute ]:user\'s manager not found, cid:', _cid, _table, dirty_data)
#    else:
#        log.warn('[ cs_sync_user_attribute ]:user not found, cid:', _cid, _table, dirty_data)

