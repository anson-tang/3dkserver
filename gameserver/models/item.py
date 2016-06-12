#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from log      import log
from errorno  import *
from constant import *

from twisted.internet       import defer


@defer.inlineCallbacks
def check_bag_capacity(user):
    ''' 检查玩家所有的背包容量 '''
    _equip_capacity = yield user.bag_equip_mgr.cur_capacity()
    if _equip_capacity >= user.base_att.equip_capacity:
        log.debug('User equip bag capacity not enough.')
        defer.returnValue( EQUIP_CAPACITY_NOT_ENOUGH )

    _equipshard_capacity = yield user.bag_equipshard_mgr.cur_capacity()
    if _equipshard_capacity >= user.base_att.equipshard_capacity:
        log.debug('User equipshard bag capacity not enough.')
        defer.returnValue( EQUIPSHARD_CAPACITY_NOT_ENOUGH )

    _treasure_capacity = yield user.bag_treasure_mgr.cur_capacity()
    if _treasure_capacity >= user.base_att.treasure_capacity:
        log.debug('User treasure bag capacity not enough.')
        defer.returnValue( TREASURE_CAPACITY_NOT_ENOUGH )

    _item_capacity = yield user.bag_item_mgr.cur_capacity()
    if _item_capacity >= user.base_att.item_capacity:
        log.debug('User item bag capacity not enough.')
        defer.returnValue( ITEM_CAPACITY_NOT_ENOUGH )

    _fellow_capacity = yield user.fellow_mgr.cur_capacity()
    if _fellow_capacity >= user.base_att.fellow_capacity:
        log.debug('User fellow bag capacity not enough.')
        defer.returnValue( FELLOW_CAPACITY_NOT_ENOUGH )

    defer.returnValue( NO_ERROR )

@defer.inlineCallbacks
def item_add_equip(user, **kwargs):
    ''' 新增装备 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')
    # 检查背包容量
    capacity_flag = kwargs.get('CapacityFlag', False)
    if capacity_flag:
        _cur_capacity = yield user.bag_equip_mgr.cur_capacity()
        if _cur_capacity >= user.base_att.equip_capacity:
            log.debug('User equip bag capacity not enough.')
            defer.returnValue( (EQUIP_CAPACITY_NOT_ENOUGH, None) )

    # 新增装备
    res_err = yield user.bag_equip_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_add_equipshard(user, **kwargs):
    ''' 新增装备碎片 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')
    # 检查背包容量
    capacity_flag = kwargs.get('CapacityFlag', False)
    if capacity_flag:
        _cur_capacity = yield user.bag_equipshard_mgr.cur_capacity()
        if _cur_capacity >= user.base_att.equipshard_capacity:
            log.debug('User equipshard bag capacity not enough.')
            defer.returnValue( (EQUIPSHARD_CAPACITY_NOT_ENOUGH, None) )

    # 新增装备碎片
    res_err = yield user.bag_equipshard_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_add_treasure(user, **kwargs):
    ''' 新增 treasure '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )
    # 新增fellow
    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')
    # 检查背包容量
    capacity_flag = kwargs.get('CapacityFlag', False)
    if capacity_flag:
        _cur_capacity = yield user.bag_treasure_mgr.cur_capacity()
        if _cur_capacity >= user.base_att.treasure_capacity:
            log.debug('User treasure bag capacity not enough.')
            defer.returnValue( (TREASURE_CAPACITY_NOT_ENOUGH, None) )

    res_err = yield user.bag_treasure_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_add_treasureshard(user, **kwargs):
    ''' 新增宝物碎片 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')

    # 新增装备碎片
    res_err = yield user.bag_treasureshard_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_add_normal_item(user, **kwargs):
    ''' 新增普通道具 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')
    # 检查背包容量
    capacity_flag = kwargs.get('CapacityFlag', False)
    if capacity_flag:
        _cur_capacity = yield user.bag_item_mgr.cur_capacity()
        if _cur_capacity >= user.base_att.item_capacity:
            log.debug('User item bag capacity not enough.')
            defer.returnValue( (ITEM_CAPACITY_NOT_ENOUGH, None) )

    # 扣宝石
    cost_credits = kwargs.get('CostCredits', 0)
    if (cost_credits > user.base_att.credits):
        log.error('user credits not enough.')
        defer.returnValue( (CHAR_CREDIT_NOT_ENOUGH, None) )
    if cost_credits:
        user.base_att.credits -= cost_credits
    # 新增道具
    res_err = yield user.bag_item_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_add_fellowsoul(user, **kwargs):
    ''' 新增伙伴分魂 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')

    # 新增伙伴分魂
    res_err = yield user.bag_fellowsoul_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_add_fellow(user, **kwargs):
    ''' 新增fellow '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )
    # 新增fellow
    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')
    # 检查背包容量
    capacity_flag = kwargs.get('CapacityFlag', False)
    if capacity_flag:
        _cur_capacity = yield user.fellow_mgr.cur_capacity()
        if _cur_capacity >= user.base_att.fellow_capacity:
            log.debug('User fellow bag capacity not enough.')
            defer.returnValue( (FELLOW_CAPACITY_NOT_ENOUGH, None) )

    user_items = []
    for i in range(0, item_num):
        # args: fellow_id, is_major, camp_id, on_troop
        res_err, attrib = yield user.fellow_mgr.create_table_data( item_id, 0, 0, 0, way_type, way_others )
        if not res_err and attrib:
            user_items.append( [attrib.attrib_id, ITEM_TYPE_FELLOW, item_id, 1] )
    defer.returnValue( (NO_ERROR, user_items) )

@defer.inlineCallbacks
def item_add_jade(user, **kwargs):
    ''' 新增玉魄 '''
    item_id = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    way_others = kwargs.get('WayOthers', '')

    # 新增玉魄
    res_err = yield user.bag_jade_mgr.new( item_id, item_num, way_type, way_others )
    defer.returnValue( res_err )


def item_add_money(user, **kwargs):
    ''' 道具货币数值 '''
    res_err = [NO_ERROR, []]
    item_id = kwargs.get('ItemID', None)
    if not item_id:
        return [UNKNOWN_ITEM_ERROR, []]
    item_num = kwargs['ItemNum']
    way_type = kwargs.get('AddType', WAY_UNKNOWN)
    # 金币
    if item_id == ITEM_MONEY_GOLDS:
        user.get_golds( item_num, way_type)
    # 宝石
    elif item_id == ITEM_MONEY_CREDITS:
        user.get_credits( item_num, way_type )
    # 精力
    elif item_id == ITEM_MONEY_ENERGY:
        user.base_att.energy += item_num
    # 仙魂
    elif item_id == ITEM_MONEY_SOUL:
        user.base_att.soul += item_num
    # 魂玉
    elif item_id == ITEM_MONEY_HUNYU:
        user.base_att.hunyu += item_num
    # 声望
    elif item_id == ITEM_MONEY_PRESTIGE:
        user.get_prestige(item_num, way_type)
    # 荣誉
    elif item_id == ITEM_MONEY_HONOR:
        user.base_att.honor += item_num
    # 斗战
    elif item_id == ITEM_MONEY_DOUZHAN:
        user.base_att.douzhan += item_num
    else:
        log.error('item_add_money. unknown item id: {0}.'.format( item_id ))
        return res_err

    res_err[0] = NO_ERROR
    res_err[1].append( [0, ITEM_TYPE_MONEY, item_id, item_num] )
    return res_err

def add_new_items(new_item, items_list):
    ''' new_item=[type, id, num]
    '''
    if not new_item or len(new_item) != 3:
        return items_list

    new_item = list(new_item)
    for _i in items_list:
        if _i[:2] == new_item[:2]:
            _i[2] += new_item[2]
            break
    else:
        items_list.append( [new_item[0], new_item[1], new_item[2]] )

    return items_list

def total_new_items(new, items_list=[]):
    ''' new=[uid, type, id, num], 其中num为道具新增的数量 '''
    if not new or len(new) != 4:
        return items_list

    new = list(new)
    for _i in items_list:
        if _i[:3] == new[:3]:
            _i[3] += new[3]
            break
    else:
        items_list.append( [new[0], new[1], new[2], new[3]] )

    return items_list

ITEM_MODELs = {
           ITEM_TYPE_MONEY: item_add_money,
        ITEM_TYPE_NECKLACE: item_add_equip,
           ITEM_TYPE_ARMOR: item_add_equip,
          ITEM_TYPE_HELMET: item_add_equip,
          ITEM_TYPE_WEAPON: item_add_equip,
      ITEM_TYPE_EQUIPSHARD: item_add_equipshard,
           ITEM_TYPE_HORSE: item_add_treasure,
         ITEM_TYPE_BOOKWAR: item_add_treasure,
      ITEM_TYPE_HORSESHARD: item_add_treasureshard,
    ITEM_TYPE_BOOKWARSHARD: item_add_treasureshard,
            ITEM_TYPE_ITEM: item_add_normal_item,
         ITEM_TYPE_PACKAGE: item_add_normal_item,
           ITEM_TYPE_CHEST: item_add_normal_item,
             ITEM_TYPE_KEY: item_add_normal_item,
        ITEM_TYPE_GOODWILL: item_add_normal_item,
  ITEM_TYPE_DIRECT_PACKAGE: item_add_normal_item,
      ITEM_TYPE_FELLOWSOUL: item_add_fellowsoul,
          ITEM_TYPE_FELLOW: item_add_fellow,
            ITEM_TYPE_JADE: item_add_jade,
     }

@defer.inlineCallbacks
def item_use_money(user, **kwargs):
    ''' 道具货币数值 '''
    item_id = kwargs.get( 'ItemID', None )
    if not item_id:
        defer.returnValue( [ UNKNOWN_ITEM_ERROR, None ] )

    res_err = [ NO_ERROR, [ [ 0, ITEM_TYPE_MONEY, item_id, 0 ] ] ]

    item_num = kwargs['ItemNum']
    #way_type = WAY_LIMIT_EXCHANGE
    way_type = kwargs.get( 'UseType', WAY_UNKNOWN )
    # 金币
    if item_id == ITEM_MONEY_GOLDS:
        res_err[0] = user.consume_golds( item_num, way_type )
        if not res_err[0]:
            res_err[1][0][3] = user.golds
    # 宝石
    elif item_id == ITEM_MONEY_CREDITS:
        res_err[0] = yield user.consume_credits( item_num, way_type )
        if not res_err[0]:
            res_err[1][0][3] = user.credits
    # 魂玉
    elif item_id == ITEM_MONEY_HUNYU:
        if user.base_att.hunyu >= item_num:
            user.base_att.hunyu -= item_num
            res_err[1][0][3] = user.base_att.hunyu
        else:
            res_err[0] = CHAR_HUNYU_NOT_ENOUGH
    else:
        log.error('item_add_money. unknown item id: {0}.'.format( item_id ))
        defer.returnValue( res_err )

    defer.returnValue( res_err )

@defer.inlineCallbacks
def item_use_normal_item(user, **kwargs):
    ''' 使用普通道具 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    _type    = kwargs['ItemType']

    err, res = yield user.bag_item_mgr.use( item_id, item_num )

    if not err:
        res = [ [ r.attrib_id, _type, item_id, r.item_num ] for r in res  ]

    defer.returnValue( ( err, res ) )

@defer.inlineCallbacks
def item_use_fellowsoul(user, **kwargs):
    ''' 使用伙伴分魂 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    item_num = kwargs['ItemNum']
    _type    = kwargs['ItemType']

    err, res = yield user.bag_fellowsoul_mgr.use( item_id, item_num )
    if not err:
        res = [ [ r.attrib_id, _type, item_id, r.item_num ] for r in res  ]

    defer.returnValue( ( err, res ) )

@defer.inlineCallbacks
def item_use_treasure(user, **kwargs):
    ''' 使用伙伴分魂 '''
    item_id  = kwargs.get('ItemID', None)
    if not item_id:
        defer.returnValue( (UNKNOWN_ITEM_ERROR, None) )

    res_err = [ NO_ERROR, [ [ 0, kwargs['ItemType'], item_id, 0 ] ] ]
    item_num = kwargs['ItemNum']

    _treasure = yield user.bag_treasure_mgr.get_item_by_item_id( item_id )
    if _treasure:
        if _treasure.item_num >= item_num:
            _treasure.item_num -= item_num

            res_err[1][0][0] = _treasure.attrib_id
            res_err[1][0][3] = _treasure.item_num
        else:
            res_err[0] = UNKNOWN_TREASURE_ERROR
    else:
        res_err[0] = UNKNOWN_TREASURE_ERROR

    defer.returnValue( res_err )

ITEM_USE_MODELs = {
           ITEM_TYPE_MONEY: item_use_money,
           ITEM_TYPE_HORSE: item_use_treasure,
         ITEM_TYPE_BOOKWAR: item_use_treasure,
            ITEM_TYPE_ITEM: item_use_normal_item,
         ITEM_TYPE_PACKAGE: item_use_normal_item,
           ITEM_TYPE_CHEST: item_use_normal_item,
             ITEM_TYPE_KEY: item_use_normal_item,
      ITEM_TYPE_FELLOWSOUL: item_use_fellowsoul,
     }



@defer.inlineCallbacks
def item_add(user, **kwargs):
    _handler = ITEM_MODELs.get( kwargs['ItemType'], None )
    if _handler:
        res = yield defer.maybeDeferred( _handler, user, **kwargs )
        defer.returnValue( res )
    else:
        log.error( 'unknown handler for item add. user:{0}, kwargs:{1}.'.format( user.cid, kwargs ) )

@defer.inlineCallbacks
def item_use(user, **kwargs):
    _handler = ITEM_USE_MODELs.get( kwargs['ItemType'], None )

    if _handler:
        res = yield defer.maybeDeferred( _handler, user, **kwargs )
        defer.returnValue( res )
    else:
        log.error( 'unknown handler for item use. user:{0}, kwargs:{1}.'.format( user.cid, kwargs ) )

@defer.inlineCallbacks
def batch_items_add(user, new_items, add_type=WAY_UNKNOWN, way_others=''):
    ''' 批量新增道具 '''
    _model_list = []
    for _type, _id, _num in new_items:
        _model = ITEM_MODELs.get(_type, None)
        if _model:
            _model_list.append( defer.maybeDeferred(_model, user, ItemID=_id, ItemNum=_num, CapacityFlag=False, AddType=add_type, WayOthers=way_others) )
        else:
            log.error('Unknown model. cid:{0}, items:{1}.'.format( user.cid, (_type, _id, _num) ))

    if not _model_list:
        defer.returnValue( [] )

    res_data = yield defer.DeferredList( _model_list )
    if not res_data:
        log.error('Unknown error. cid:{0}, new_items:{1}, res_data: {2}.'.format( user.cid, new_items, res_data ))
        res_data = []
    defer.returnValue( res_data )




