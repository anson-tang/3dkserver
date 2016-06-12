#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author:
# License: 
# Summary: 

#import random
#
#from time     import time
#from log      import log
#from time     import time
#from constant import *
#from errorno  import *
#from system   import get_cardpool_shrine_levels, get_cardpool_start_levels, get_cardpool_conf, get_randcard_consume_conf, get_fellow_by_fid
#
#from table_fields     import TABLE_FIELDS
#from syslogger        import syslogger
#from twisted.internet import defer
#from protocol_manager import cs_call, gw_broadcast
#
#
#class RandCardManager(object):
#    def __init__(self):
#        self.tbl_cardpool = []
#
#    @defer.inlineCallbacks
#    def randCard(self, user, card_type, rand_times):
#        '''
#        @return : err, credits, res_fellow_list
#        '''
#        res_err = [REQUEST_LIMIT_ERROR, 0, [], []]
#        _item   = None
#
#        shrine = user.getShrine(card_type)
#        if None == shrine:
#            defer.returnValue( res_err )
#
#        # 抽卡消耗的配置
#        _consume = get_randcard_consume_conf( card_type )
#        if not _consume:
#            log.error('Can not find conf.')
#            res_err[0] = NOT_FOUND_CONF
#            defer.returnValue( res_err )
#
#        # 检查抽卡条件是否满足
#        if (_consume['ItemType'] == ITEM_TYPE_MONEY):
#            if (shrine.free_timestamp_left > 0) or rand_times > 1:
#                if (user.base_att.credits < _consume['ItemNum']*rand_times):
#                    log.error("cur credits: {0}, need credits: {1}.".format( user.base_att.credits, _consume['ItemNum']*rand_times))
#                    res_err[0] = CHAR_CREDIT_NOT_ENOUGH
#                    defer.returnValue( res_err )
#        elif (_consume['ItemType'] == ITEM_TYPE_ITEM):
#            total_num, item_attribs = yield user.bag_item_mgr.get_items( _consume['ItemID'] )
#            if (_consume['ItemNum'] * rand_times) > total_num:
#                log.error('item id: {0}, need num: {1}, cur num: {2}.'.format( _consume['ItemID'], (_consume['ItemNum'] * rand_times), total_num ))
#                res_err[0] = CHAR_ITEM_NOT_ENOUGH
#                defer.returnValue( res_err )
#        else:
#            log.error('Unknown item type: {0}.'.format( _consume['ItemType'] ))
#            res_err[0] = RANDCARD_TYPE_ERROR
#            defer.returnValue( res_err )
#
#        # 获取抽卡池
#        pool = self.GetCardPool( card_type, shrine, user.level )
#        if not pool:
#            res_err[0] = RANDCARD_NO_POOL_CFG
#            defer.returnValue( res_err )
#        # 使用的道具的剩余信息
#        items_return = []
#        get_card_list = []
#        for i in range(0, rand_times):
#            (err, card) = self.randCardFromPool( pool )
#            if err:
#                log.error('Rand card from pool fail!')
#                continue
#
#            # 消耗道具或者钻石
#            if (_consume['ItemType'] == ITEM_TYPE_MONEY):
#                if (shrine.free_timestamp_left > 0):
#                    # 扣钻石
#                    if (user.base_att.credits < _consume['ItemNum']):
#                        log.error("cur_credits: {0}, need_credits: {1}.".format( user.base_att.credits, _consume['ItemNum'] ))
#                        break
#                    user.base_att.credits  -= _consume['ItemNum']
#            elif (_consume['ItemType'] == ITEM_TYPE_ITEM):
#                # 扣道具
#                err, used_attribs = yield user.bag_item_mgr.use( _consume['ItemID'], 1 )
#                if err:
#                    log.error('Use item error.')
#                    res_err[0] = err
#                    defer.returnValue( res_err )
#                # used_attribs-已使用的道具
#                for _a in used_attribs:
#                    items_return.append( [_a.attrib_id, _a.item_type, _a.item_id, _a.item_num] )
#            # 先扣除再给予原则
#            get_card_list.append(card)
#            # 更新玩家的shrine数据, 含rand_count, shrine_level, 及shrine升级后更新pool
#            _levelup = shrine.add( _consume['FreeTime'] )
#            if _levelup:
#                pool = self.GetCardPool( card_type, shrine, user.level )
#
#        msg_fellow_ids = [] # 走马灯通告的fellow_ids
#        fellow_id_list = []
#        new_attribs    = []
#        for card in get_card_list:
#            fellow_id = card['ItemId']
#            fellow_id_list.append(fellow_id)
#            try:
#                # args: fellow_id, is_major, camp_id, on_troop
#                err, attrib = yield user.fellow_mgr.create_table_data( fellow_id, 0, 0, 0 )
#            except Exception as e:
#                log.warn('Create fellow fail! e:', e)
#                defer.returnValue(res_err)
#
#            if not err:
#                new_attribs.append( [attrib.attrib_id, fellow_id] )
#                _conf = get_fellow_by_fid( fellow_id )
#                if _conf and _conf['Quality'] == 3:
#                    msg_fellow_ids.append( attrib.attrib_id )
#        # 情缘抽到紫卡, 全服广播
#        if card_type    == CARD_SHRINE_GREEN:
#            _type_name  = RANDCARD_TYPE_GREEN
#        elif card_type  == CARD_SHRINE_BLUE:
#            _type_name  = RANDCARD_TYPE_BLUE
#        elif rand_times == 10:
#            _type_name  = RANDCARD_TYPE_TEN
#        else:
#            _type_name  = RANDCARD_TYPE_PURPLE
#
#        if msg_fellow_ids:
#            message = [RORATE_MESSAGE_ACHIEVE, [ACHIEVE_TYPE_RANDCARD, [user.base_att.nick_name, _type_name, fellow_id_list]]]
#            gw_broadcast('sync_broadcast', [message])
#
#        defer.returnValue( (NO_ERROR, user.base_att.credits, new_attribs, items_return) )
#
#    def GetCardPool(self, card_type, shrine, char_level):
#        #Use which pool to rand bonus?
#
#        _shrine_level =  shrine.level
#        _rand_count   = shrine.rand_count
#        _last_time    = shrine.last_rand_time
#
#        # 累积抽卡次数=0的时候，读取当前level+1配置表
#        if 0 == _rand_count:
#            _shrine_level += 1
#
#            _all_shrine_levels = get_cardpool_shrine_levels(card_type)
#            while _shrine_level not in _all_shrine_levels:
#                _shrine_level -= 1
#                if _shrine_level in _all_shrine_levels:
#                    break
#                if _shrine_level < 0:
#                    break
#            # 未找到cardpool
#            if _shrine_level < 0:
#                return []
#        else:
#            _shrine_level = 0
#        # 随机时，读取最接近玩家等级的配置
#        _pool_start_level = 1
#        _all_start_levels = get_cardpool_start_levels(card_type, _shrine_level)
#        for _start_level in _all_start_levels:
#            if _pool_start_level <= _start_level and _start_level <= char_level:
#                _pool_start_level = _start_level
#
#        return get_cardpool_conf(card_type, _shrine_level, _pool_start_level)
#
#    def randCardFromPool(self, pool):
#        '''
#        @return: ( errno, (CardInPool) )
#        这里是权重, 非概率
#        '''
#        cardpool = []
#        for _id, _value in pool.iteritems():
#            cardpool.extend( [_id] * _value['Rate'] )
#
#        if cardpool:
#            rand_id = random.choice( cardpool )
#            return (NO_ERROR, pool[rand_id])
#        else:
#            log.warn('Can not find fit card in pool!')
#            return (RANDCARD_NO_POOL_CFG, () )
#
#
#    #def randCardFromPool(self, pool):
#    #    '''
#    #    @return: ( errno, (CardInPool) )
#    #    这里是权重, 非概率
#    #    '''
#    #    total_weight = 0 #Optimize later, store it on mgr
#    #    for card in pool:
#    #        total_weight += int(card['Rate'])
#
#    #    rand_pos = random.randint(0, total_weight)
#
#    #    last_visit_pos = 0
#    #    for card in pool:
#    #        new_visit_pos = last_visit_pos + int(card['Rate'])            
#    #        if last_visit_pos <= rand_pos and rand_pos <= new_visit_pos:
#    #            return (NO_ERROR, (card))
#    #        last_visit_pos = new_visit_pos
#
#    #    log.warn('Can not find fit card in pool!')
#    #    return (RANDCARD_NO_POOL_CFG, () )
#            
#
#g_RandCardManager = RandCardManager()

