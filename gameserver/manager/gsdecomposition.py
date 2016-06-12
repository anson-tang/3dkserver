#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from log      import log
from errorno  import *
from constant import *
from json     import loads, dumps

from syslogger              import syslogger
from twisted.internet       import defer
from system                 import get_fellow_decomposition, get_fellow_by_fid, get_roleexp_by_level, get_item_by_itemid, get_item_decomposition, get_treasure_exp_conf, get_fellow_advanced, get_treasure_refine_conf, get_fellow_reborn_conf, get_treasure_reborn_conf
from utils                  import split_items
from models.item            import *

from math                   import ceil


class GSDecompositionMgr(object):
    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

    @defer.inlineCallbacks
    def decomposition(self, decomposition_type, user_ids):
        '''
        @summary: 1：炼化武将，2：炼化装备，3：炼化宝物
        '''
        res_err = UNKNOWN_ERROR
        if decomposition_type == 1:
            res_err = self.fellow_decomposition( user_ids )
        elif decomposition_type == 2:
            res_err = yield self.equip_decomposition( user_ids )
        elif decomposition_type == 3:
            res_err = yield self.treasure_decomposition( user_ids )

        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def batch_decompose(self, credits):
        user_fellow_ids = yield self.user.fellow_mgr.ids_green

        if user_fellow_ids:
            credits_need = int(ceil(len(user_fellow_ids) / float(BATCH_DECOMPOSE_PRICE)))
            if credits_need < credits:
                credits_need = credits

            res = yield self.user.consume_credits(credits_need, WAY_BATCH_DECOMPOSE)
            if not res:
                defer.returnValue((self.user.credits, self.fellow_decomposition(user_fellow_ids)))
            else:
                defer.returnValue(res)
        else:
            defer.returnValue(NO_ANY_GREEN_FELLOW)

    def fellow_decomposition(self, user_fellow_ids):
        ''' 
        @summary: 伙伴炼化 
            (1) 已上阵 或 进阶等级大于0的不可炼化, 需要先重生
            (2) 炼化产出道具, 读sysconfig['fellow_decomposition'], 返还金币, 仙魂, 魂玉
            (3) 读sysconfig['roleexp'], 返还强化消耗的经验
            (4) 1点经验=1个金币,  1点经验=1点仙魂, 返还金币、仙魂
            (4) 删除用于炼化的材料, 即伙伴
        '''
        for _ufid in user_fellow_ids:
            attrib = self.user.fellow_mgr.get_fellow( _ufid )
            if not attrib:
                log.error('Can not find user fellow. user_fellow_id: {0}.'.format( _ufid ))
                return UNKNOWN_FELLOW_ERROR
                #defer.returnValue( UNKNOWN_FELLOW_ERROR )
            # 已上阵 或 进阶等级大于0的不可炼化, 需要先重生
            if attrib.camp_id > 0 or attrib.advanced_level > 0:
                log.error('Fellow advanced level error. ufid: {0}, camp_id: {1}, ad_lvl: {2}.'.format( _ufid, attrib.camp_id, attrib.advanced_level ))
                return FELLOW_DECOMPOSITION_ERROR
            fellow_conf = get_fellow_by_fid( attrib.fellow_id )
            if not fellow_conf:
                log.error('Can not find fellow conf. fellow id: {0}.'.format( attrib.fellow_id ))
                return NOT_FOUND_CONF
                #defer.returnValue( NOT_FOUND_CONF )

        total_golds, total_soul, total_hunyu = 0, 0, 0
        for _ufid in user_fellow_ids:
            attrib = self.user.fellow_mgr.get_fellow( _ufid )
            if not attrib:
                log.error('Unknown fellow. _ufid: {0}.'.format( _ufid ))
                continue
            fellow_conf = get_fellow_by_fid( attrib.fellow_id )
            # 炼化产出道具
            decomposition_conf = get_fellow_decomposition( fellow_conf['QualityLevel'] )
            if decomposition_conf:
                items_list = split_items( decomposition_conf['ItemList'] )
                for _type, _id, _num in items_list:
                    if _type != ITEM_TYPE_MONEY:
                        log.error('Unknown decomposition item type. item type: {0}.'.format( _type ))
                        continue
                    if _id == ITEM_MONEY_GOLDS:
                        total_golds += _num
                    elif _id == ITEM_MONEY_SOUL:
                        total_soul  += _num
                    elif _id == ITEM_MONEY_HUNYU:
                        total_hunyu += _num

            # 删除用于炼化的fellow
            self.user.fellow_mgr.delete_table_data( _ufid )
            # add syslog
            syslogger(LOG_FELLOW_DECOMPOSITION, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _ufid, attrib.fellow_id, fellow_conf['QualityLevel'], fellow_conf['Star'])

            # 返还仙魂、金币
            extra_exp   = fellow_conf['Exp'] + attrib.exp
            quality     = fellow_conf['Quality']
            # 返还伙伴强化消耗的经验
            for _level in range(fellow_conf['Level'], attrib.level):
                _conf = get_roleexp_by_level( _level )
                _exp  = _conf.get( FELLOW_QUALITY[quality], 0 )
                if not _exp:
                    continue
                extra_exp += _exp
            # 1点经验, 等于1个金币, 等于1点仙魂
            total_golds += extra_exp
            total_soul  += extra_exp

        # 返还仙魂、金币、魂玉
        items_return = []
        if total_golds > 0:
            self.user.base_att.golds += total_golds
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, total_golds] )
        if total_soul > 0:
            self.user.base_att.soul  += total_soul 
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_SOUL, total_soul] )
        if total_hunyu > 0:
            self.user.base_att.hunyu += total_hunyu
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_HUNYU, total_hunyu] )
 
        return items_return

    @defer.inlineCallbacks
    def equip_decomposition(self, user_equip_ids):
        ''' 
        @summary: 装备炼化 
            (1) 已穿戴 或 洗炼属性大于0的不可炼化, 需要先重生
            (2) 炼化产出道具, 读sysconfig['item_decomposition'], 返还道具
            (3) 返还强化消耗的金币
            (4) 删除用于炼化的材料, 即装备
        '''
        for _ueid in user_equip_ids:
            equip = yield self.user.bag_equip_mgr.get( _ueid )
            if not equip:
                log.error('Can not find user equip. user_equip_id: {0}.'.format( _ueid ))
                defer.returnValue( UNKNOWN_EQUIP_ERROR )

            # 已穿戴 或 洗炼属性大于0的不可炼化, 需要先重生
            if (equip.camp_id > 0):
                log.error('Equip refine level error. ueid: {0}, camp_id: {1}, refine_attr: {2}.'.format( _ueid, equip.camp_id, loads(equip.refine_attribute) ))
                defer.returnValue( EQUIP_DECOMPOSITION_ERROR )

            for _attr in loads(equip.refine_attribute):
                if _attr[1] > 0:
                    defer.returnValue( EQUIP_DECOMPOSITION_ERROR )

            # 装备的conf
            equip_conf = get_item_by_itemid( equip.item_id )
            if not equip_conf:
                log.error('Can not find conf. item id: {0}.'.format( equip.item_id ))
                defer.returnValue( UNKNOWN_ITEM_ERROR )

        items_return = []
        total_golds  = 0
        for _ueid in user_equip_ids:
            equip = yield self.user.bag_equip_mgr.get( _ueid )
            equip_conf = get_item_by_itemid( equip.item_id )
            # 返还强化消耗的金币
            total_golds += equip.strengthen_cost

            # 炼化产出的道具
            decomposition_conf = get_item_decomposition( equip.item_type, equip_conf['QualityLevel'] )
            for _dec in decomposition_conf:
                items_list = split_items( _dec['ItemList'] )
                for _type, _id, _num in items_list:
                    # character attribute需要单独处理
                    if _type == ITEM_TYPE_MONEY:
                        if _id == ITEM_MONEY_GOLDS:
                            total_golds += _num
                        continue
                    model = ITEM_MODELs.get( _type, None )
                    if not model:
                        log.error('Unknown decomposition item type. item type: {0}.'.format( _type ))
                        continue
                    res_err, res_value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_EQUIP_DECOMPOSITION, CapacityFlag=False)
                    if not res_err:
                        for _v in res_value:
                            items_return = total_new_items(_v, items_return)
            # 删除用于炼化的equip
            self.user.bag_equip_mgr.delete_table_data( _ueid )
            # add syslog
            syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _ueid, equip.item_id, 1, WAY_EQUIP_DECOMPOSITION)

        # 返还金币
        if total_golds > 0:
            #self.user.base_att.golds += total_golds
            self.user.get_golds( total_golds, WAY_EQUIP_REFINE )
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, total_golds] )

        defer.returnValue( items_return )

    @defer.inlineCallbacks
    def treasure_decomposition(self, user_treasure_ids):
        ''' 
        @summary: 宝物炼化 相同类型
            (1) 已穿戴 或 精炼属性大于0的不可炼化, 需要先重生, 经验马 经验书不能也炼化
            (2) 炼化产出道具, 读sysconfig['item_decomposition'], 返还道具
            (3) 返还宝物强化消耗的经验, 并将其折算成经验马或经验书, 返还金币
            (4) 删除用于炼化的材料, 即宝物
        '''
        for _utid in user_treasure_ids:
            treasure = yield self.user.bag_treasure_mgr.get( _utid )
            if not treasure:
                log.error('Can not find user treasure. user_treasure_id: {0}.'.format( _utid ))
                defer.returnValue( UNKNOWN_TREASURE_ERROR )
            # 所选宝物 类型必须为书或马
            if treasure.item_type not in BAG_TREASURE:
                log.error('Selected treasure type not horse or bookwar.')
                defer.returnValue( UNKNOWN_TREASURE_ERROR )
            # 经验马、经验书不能炼化
            if treasure.item_id == EXP_HORSE_ID or treasure.item_id == EXP_BOOKWAR_ID:
                log.error('EXP_HORSE or EXP_BOOKWAR could not be decomposition. item id: {0}.'.format( treasure.item_id ))
                defer.returnValue( TREASURE_DECOMPOSITION_ERROR )

            # 已穿戴 或 精炼属性大于0的不可炼化, 需要先重生
            if treasure.camp_id > 0 or treasure.refine_level > 0:
                log.error('Treasure refine level error. ufid: {0}, refine level: {1}.'.format( _utid, treasure.refine_level ))
                defer.returnValue( TREASURE_DECOMPOSITION_ERROR )

            # 宝物的conf
            treasure_conf = get_item_by_itemid( treasure.item_id )
            if not treasure_conf:
                log.error('Can not find conf. item id: {0}.'.format( treasure.item_id ))
                defer.returnValue( UNKNOWN_ITEM_ERROR )

        total_golds, horse_exp, bookwar_exp = 0, 0, 0
        items_return = []
        for _utid in user_treasure_ids:
            treasure  = yield self.user.bag_treasure_mgr.get( _utid )
            extra_exp = treasure.exp
            treasure_conf = get_item_by_itemid( treasure.item_id )
            # 宝物自身经验
            for _attr in treasure_conf['attributes']:
                if _attr['AttributeID'] in (ATTRIBUTE_TYPE_HORSE_EXP, ATTRIBUTE_TYPE_BOOKWAR_EXP):
                    extra_exp += _attr['Value']
                    break

            # 炼化产出的道具
            decomposition_conf = get_item_decomposition( treasure.item_type, treasure_conf['QualityLevel'] )
            for _dec in decomposition_conf:
                items_list = split_items( _dec['ItemList'] )
                #log.info('For Test. _utid: {0}, items_list: {1}.'.format( _utid, items_list ))
                for _type, _id, _num in items_list:
                    # 货币类型特殊处理
                    if _type == ITEM_TYPE_MONEY:
                        if _id == ITEM_MONEY_GOLDS:
                            total_golds += _num
                        continue
                    model = ITEM_MODELs.get( _type, None )
                    if not model:
                        log.error('Unknown decomposition item type. item type: {0}.'.format( _type ))
                        continue
                    res_err, res_value = model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_TREASURE_DECOMPOSITION, CapacityFlag=False)
                    if not res_err:
                        for _v in res_value:
                            items_return = total_new_items(_v, items_return)

            # 返还宝物强化消耗的经验, 并折算成经验马或经验书
            for _level in range(1, treasure.level + 1):
                _conf = get_treasure_exp_conf( _level )
                extra_exp += _conf.get( ITEM_STRENGTHEN_COST[treasure_conf['Quality']], 0 )
            if treasure.item_type == ITEM_TYPE_HORSE:
                horse_exp += extra_exp
            else:
                bookwar_exp += extra_exp

            # 删除用于炼化的treasure
            self.user.bag_treasure_mgr.delete_table_data( _utid )
            # add syslog
            syslogger(LOG_ITEM_LOSE, self.cid, self.user.level, self.user.vip_level, self.user.alliance_id, _utid, treasure.item_id, 1, WAY_TREASURE_DECOMPOSITION)

        # 返还金币
        total_golds += (horse_exp + bookwar_exp) * TREASURE_STRENGTHEN_EXP_TO_GOLDS
        #self.user.base_att.golds += total_golds
        self.user.get_golds( total_golds, WAY_TREASURE_REFINE )
        # 用经验值兑换经验马或经验书
        if horse_exp > 0:
            res_err, res_value = yield self.user.bag_treasure_mgr.add_exp_treasure( ITEM_TYPE_HORSE, horse_exp )
            if not res_err:
                for _v in res_value:
                    items_return = total_new_items(_v, items_return)
        if bookwar_exp > 0:
            res_err, res_value = yield self.user.bag_treasure_mgr.add_exp_treasure( ITEM_TYPE_BOOKWAR, bookwar_exp )
            if not res_err:
                for _v in res_value:
                    items_return = total_new_items(_v, items_return)
        if total_golds > 0:
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, total_golds] )

        defer.returnValue( items_return )


class GSRebornMgr(object):
    def __init__(self, user):
        self.user = user
        self.cid  = user.cid

    @defer.inlineCallbacks
    def reborn(self, reborn_type, user_id):
        '''
        @summary: 重生的类型：1. 伙伴，2：装备，3：宝物。
        '''
        res_err = UNKNOWN_ERROR
        if reborn_type == 1:
            res_err = yield self.fellow_reborn( user_id )
        elif reborn_type == 2:
            res_err = yield self.equip_reborn( user_id )
        elif reborn_type == 3:
            res_err = yield self.treasure_reborn( user_id )

        defer.returnValue( res_err )

    @defer.inlineCallbacks
    def fellow_reborn(self, user_fellow_id):
        ''' 
        @summary: 伙伴重生 
            (1) 已上阵 或 未进阶的伙伴 不能重生
            (2) 重生后，进阶等级和强化等级清零, 全额返还该伙伴进阶消耗的道具总数和强化消耗的仙魂、金币, 
            (3) 进阶消耗的金币不返还
        '''
        attrib = self.user.fellow_mgr.get_fellow( user_fellow_id )
        if not attrib:
            log.error('Can not find user fellow. user_fellow_id: {0}.'.format( user_fellow_id ))
            defer.returnValue( UNKNOWN_FELLOW_ERROR )

        fellow_conf = get_fellow_by_fid( attrib.fellow_id )
        if not fellow_conf:
            log.error('Can not find fellow conf. fellow id: {0}.'.format( attrib.fellow_id ))
            defer.returnValue( NOT_FOUND_CONF )

        # 已上阵 或 未进阶的伙伴 不可重生
        if attrib.camp_id > 0 or attrib.advanced_level == 0:
            log.error('Fellow advanced level or camp id error. ufid: {0}, ad_lvl: {1}, camp id: {2}.'.format( user_fellow_id, attrib.advanced_level, attrib.camp_id ))
            defer.returnValue( FELLOW_REBORN_ERROR )

        # 判断钻石消耗
        reborn_conf = get_fellow_reborn_conf( fellow_conf['QualityLevel'], attrib.advanced_level )
        if not reborn_conf:
            log.error('Unknown reborn conf. qLevel: {0}, ad_level: {1}.'.format( fellow_conf['QualityLevel'], attrib.advanced_level ))
            defer.returnValue( NOT_FOUND_CONF )
        # 玩家钻石不足
        if self.user.base_att.credits < reborn_conf['Cost']:
            log.error('Need credits: {0}, cur credits: {1}.'.format( reborn_conf['Cost'], self.user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )
        # 扣钻石
        #self.user.base_att.credits -= reborn_conf['Cost']
        if reborn_conf['Cost']:
            yield self.user.consume_credits( reborn_conf['Cost'], WAY_FELLOW_REBORN )
        # 返还仙魂、金币
        extra_exp   = fellow_conf['Exp'] + attrib.exp
        quality     = fellow_conf['Quality']
        # 返还伙伴强化消耗的经验
        for _level in range(fellow_conf['Level'], attrib.level):
            _conf = get_roleexp_by_level( _level )
            _exp  = _conf.get( FELLOW_QUALITY[quality], 0 )
            if not _exp:
                continue
            extra_exp += _exp
        # 增加1点经验, 需要消耗1个金币,  每1点仙魂, 可以增加1点经验
        #self.user.base_att.golds += extra_exp
        self.user.get_golds( extra_exp, WAY_FELLOW_REBORN )
        self.user.base_att.soul  += extra_exp

        # 返还伙伴进阶消耗的道具
        items_list = []
        for _a_level in range(1, attrib.advanced_level+1):
            advanced_conf = get_fellow_advanced( attrib.fellow_id, _a_level )
            if not advanced_conf:
                log.error('Can not find fellow advanced conf. fellow id: {0}, advanced_level: {1}.'.format( attrib.fellow_id, _a_level ))
                continue
            _list = split_items( advanced_conf['ItemList'] )
            for _l in _list:
                items_list = add_new_items( _l, items_list )
        #log.info('For Test. refine_level: {0}, items_list: {1}.'.format( attrib.advanced_level, items_list ))

        items_return = []
        for _type, _id, _num in items_list:
            # 货币类型特殊处理
            if _type == ITEM_TYPE_MONEY:
                continue
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown reborn item type. item type: {0}.'.format( _type ))
                continue
            res_err, res_value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_FELLOW_REBORN, CapacityFlag=False)
            if not res_err:
                for _v in res_value:
                    items_return = total_new_items(_v, items_return)
        # 进阶等级和强化等级、经验清零
        attrib.level = fellow_conf['Level']
        attrib.exp, attrib.advanced_level = 0, 0
        if extra_exp > 0:
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, extra_exp] )
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_SOUL, extra_exp] )

        defer.returnValue( (self.user.base_att.credits, items_return) )

    @defer.inlineCallbacks
    def equip_reborn(self, user_equip_id):
        ''' 
        @summary: 装备重生 
            (1) 已穿戴 或 未洗炼的装备 不能重生
            (2) 返还该装备洗炼消耗的洗炼石和强化消耗的金币
            (3) 洗练消耗的金币和钻石不返还
            (4) 每返还10个洗炼石，则重生价格为1钻石
        '''
        equip = yield self.user.bag_equip_mgr.get( user_equip_id )
        if not equip:
            log.error('Can not find user equip.')
            defer.returnValue( UNKNOWN_EQUIP_ERROR )

        # 已穿戴 或 洗炼属性为[]的不可重生
        #log.error('camp_id: {0}, refine_attribute: {1}.'.format( equip.camp_id, loads(equip.refine_attribute) ))
        if (equip.camp_id > 0) or not loads(equip.refine_attribute):
            log.error('Equip reborn error. cid: {0}, ueid: {1}, camp_id: {2}, refine_attribute: {3}.'.format( self.cid, user_equip_id, equip.camp_id, loads(equip.refine_attribute) ))
            defer.returnValue( EQUIP_REBORN_ERROR )

        # 装备的conf
        equip_conf = get_item_by_itemid( equip.item_id )
        if not equip_conf:
            log.error('Can not find conf. item id: {0}.'.format( equip.item_id ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )

        # 计算钻石消耗
        if (equip.refine_cost % 10) > 0:
            need_credits = equip.refine_cost / 10 + 1
        else:
            need_credits = equip.refine_cost / 10

        # 玩家钻石不足
        if need_credits > self.user.base_att.credits:
            log.error('Need credits: {0}, now have: {1}.'.format( need_credits, self.user.base_att.credits ))
            defer.returnValue( CHAR_CREDIT_NOT_ENOUGH )

        items_return = []
        # 返还金币、洗炼石
        #self.user.base_att.golds += equip.strengthen_cost
        self.user.get_golds( equip.strengthen_cost, WAY_EQUIP_REBORN )
        try:
            res_err, res_value = yield self.user.bag_item_mgr.new(ITEM_REFINE_STONE, equip.refine_cost)
            if not res_err:
                items_return = res_value
        except Exception as e:
            log.error('ERROR: {0}.'.format( e ))
            log.exception()
        # 扣钻石, 数据清零
        #self.user.base_att.credits -= need_credits
        if need_credits:
            yield self.user.consume_credits( need_credits, WAY_EQUIP_REBORN )
        self.user.bag_equip_mgr.reborn( user_equip_id )
 
        if equip.strengthen_cost > 0:
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, equip.strengthen_cost] )

        # 强化、精炼属性清零
        equip.level, equip.strengthen_cost, equip.refine_cost, equip.refine_attribute = 0, 0, 0, dumps([])

        defer.returnValue( (self.user.base_att.credits, items_return) )

    @defer.inlineCallbacks
    def treasure_reborn(self, user_treasure_id):
        '''
        @summary: 宝物重生 
            (1) 已穿戴 或 未精炼的宝物 不能重生
            (2) 返还该宝物精炼消耗的道具和强化消耗的经验道具, 强化消耗的道具返还为经验宝物 
            (3) 精炼消耗的金币不返还 
        '''
        treasure = yield self.user.bag_treasure_mgr.get( user_treasure_id )
        if not treasure:
            log.error('Can not find user treasure.')
            defer.returnValue( UNKNOWN_TREASURE_ERROR )
        # 已穿戴 或 未精炼的宝物不可重生
        if treasure.camp_id > 0 or treasure.refine_level <= 0:
            log.error('Treasure reborn error. camp_id: {0}, refine level: {1}.'.format( treasure.camp_id, treasure.refine_level ))
            defer.returnValue( TREASURE_REBORN_ERROR )

        # 宝物的conf
        treasure_conf = get_item_by_itemid( treasure.item_id )
        if not treasure_conf:
            log.error('Can not find conf. item id: {0}.'.format( treasure.item_id ))
            defer.returnValue( UNKNOWN_ITEM_ERROR )
        total_exp = treasure.exp

        # 扣钻石
        reborn_conf = get_treasure_reborn_conf( treasure_conf['QualityLevel'], treasure.refine_level )
        if reborn_conf:
            yield self.user.consume_credits( reborn_conf['Cost'], WAY_TREASURE_REBORN )

        # 返还宝物强化消耗的经验
        for _level in range( 1, treasure.level + 1):
            _conf = get_treasure_exp_conf( _level )
            _exp  = _conf.get( ITEM_STRENGTHEN_COST[treasure_conf['Quality']], 0 )
            if not _exp:
                continue
            total_exp += _exp
 
        # 用经验值兑换经验马或经验书, 增加1点经验, 需要消耗5个金币
        total_golds = total_exp * TREASURE_STRENGTHEN_EXP_TO_GOLDS
        self.user.get_golds( total_golds, WAY_TREASURE_REBORN )

        items_return = []
        _err, _value = yield self.user.bag_treasure_mgr.add_exp_treasure( treasure.item_type, total_exp )
        if not _err:
            items_return = _value

        # 返还精炼消耗的道具
        items_list = [] # 消耗的道具列表
        for _refine_level in range(1, treasure.refine_level + 1):
            refine_conf = get_treasure_refine_conf(treasure.item_id, _refine_level)
            if not refine_conf:
                log.error('Can not find refine conf. item_id: {0}, refine_level: {1}.'.format( treasure.item_id, _refine_level ))
                continue
            _list = split_items( refine_conf['CostItemList'] )
            for _l in _list:
                items_list = add_new_items( _l, items_list )
        #log.info('For Test. refine_level: {0}, items_list: {1}.'.format( treasure.refine_level, items_list ))

        # 道具类型格式:道具ID:道具数量
        for _type, _id, _num in items_list:
            # 货币类型特殊处理
            if _type == ITEM_TYPE_MONEY:
                continue
            model = ITEM_MODELs.get( _type, None )
            if not model:
                log.error('Unknown reborn item type. item type: {0}.'.format( _type ))
                continue
            res_err, res_value = yield model(self.user, ItemID=_id, ItemNum=_num, AddType=WAY_TREASURE_REBORN, CapacityFlag=False)
            if not res_err:
                for _v in res_value:
                    items_return = total_new_items(_v, items_return)

        # 强化、精炼属性清零
        treasure.level, treasure.exp, treasure.refine_level = 0, 0, 0
        if total_golds > 0:
            items_return.append( [0, ITEM_TYPE_MONEY, ITEM_MONEY_GOLDS, total_golds] )
 
        defer.returnValue( (self.user.base_att.credits, items_return) )


