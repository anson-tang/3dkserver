#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from datetime       import datetime
from systemdata     import load_all_config
from log import log

from constant import *

sysconfig = load_all_config(FOR_SERVER_ONLY)

def get_randcard_consume_conf(card_type):
    ''' 抽奖池不同类型的消耗配置 '''
    _conf = sysconfig.get('randcard_consume', {})
    return _conf.get(card_type, {})

def get_randcard_max_level(card_type):
    '''获取神坛的最高等级
    '''
    _conf = sysconfig.get('randcard_level', {})
    shrine_levels = _conf.keys()
    _max_level    = 0 # 神坛的level从0级开始
    if len(shrine_levels) > 0:
        _max_level = max(shrine_levels)
    return _max_level 

def get_randcard_level_count(shrine_level, card_type):
    '''神坛升级的抽卡次数配置
    '''
    _conf = sysconfig.get('randcard_level', {})
    if _conf.has_key(shrine_level) and len(_conf[shrine_level]) >= 4:
        return _conf[shrine_level][card_type]
    else:
        log.error('Can not find conf. shrine_level: {0}, card_type: {1}'.format( shrine_level, card_type ))
        return 0

def get_cardpool_conf(card_type, shrine_level, start_level):
    '''get cardpool by (card type and shrine level and start_level)
    '''
    _conf = sysconfig.get('cardpool', {})
    if _conf.has_key(card_type) and \
            _conf[card_type].has_key(shrine_level) and \
            _conf[card_type][shrine_level].has_key(start_level):
        return _conf[card_type][shrine_level][start_level]
    else:
        log.error('get_cardpool_conf. Can not find conf. shrine_level: {0}, card_type: {1}, start_level: {2}.'.format( shrine_level, card_type, start_level ))
        return {}

def get_cardpool_shrine_levels(card_type):
    '''get all shrine levels by card type.
    '''
    _conf = sysconfig.get('cardpool', {})
    return _conf.get(card_type, {}).keys()

def get_cardpool_start_levels(card_type, shrine_level):
    '''get all start levels by (card type and shrine level)
    '''
    _conf = sysconfig.get('cardpool', {})
    if _conf.has_key(card_type) and _conf[card_type].has_key(shrine_level):
        return _conf[card_type][shrine_level].keys()
    else:
        log.error('Can not find conf. shrine_level: {0}, card_type: {1}.'.format( shrine_level, card_type ))
        return []

def get_campcard_cost_conf(rand_time):
    _conf = sysconfig.get('campcard_cost', {})
    return _conf.get(rand_time, {}).get('RandCost', 0)

def get_campcard_pool_conf(camp_id, rand_time):
    _conf = sysconfig.get('campcard_pool', {})
    return _conf.get(camp_id, {}).get(rand_time, {})

def get_all_monster():
    return sysconfig.get('monster', {})

def get_monster_by_monsterid(monster_id):
    '''get monster by monster id
    '''
    _conf = sysconfig.get('monster', {})
    return _conf.get(monster_id, {})

def get_monster_conf(dungeon_id, dungeon_star):
    '''get monster by dungeon id and star
    '''
    _conf = sysconfig.get('monster', {})
    return _conf.get(dungeon_id, {}).get(dungeon_star, {})

def get_drop_conf(dungeon_id, dungeon_star):
    ''' get all drop by dungeon id 
        {monsterid:{diffID:{dropID:dict_data},...},...}
    '''
    _all_conf = sysconfig.get('monster_drop', {})
    _oss_conf = sysconfig.get('monster_drop_oss', {})
    _normal_conf = _all_conf.get(dungeon_id, {}).get(dungeon_star, {})
    _oss_confs = _oss_conf.get(dungeon_id, {}).get(dungeon_star, {})
    _conf = dict(_normal_conf.items()+_oss_confs.items())
    data = {}
    for _dropID, _dict_data in _conf.iteritems():
        if _dict_data.get("ActiveID", 0) !=0:
            if check_excite_activity_status(_dict_data.get("ActiveID", 0)):
                data[_dropID] = _dict_data
        else:
            data[_dropID] = _dict_data
    return data

def get_all_scene():
    return sysconfig.get('scene', {})

def get_scene_conf(scene_id):
    _conf = sysconfig.get('scene', {})
    return _conf.get(scene_id, {})

def get_scene_star_reward(scene_id, scene_star_count):
    _conf = sysconfig.get('scene_star_reward', {})
    return _conf.get(scene_id, {}).get(scene_star_count, {})

def get_scene_sweep_cost_conf(reset_time):
    _conf =  sysconfig.get('scene_sweep_cost', {})
    if not _conf:
        return 0
    if _conf.has_key(reset_time):
        return _conf[reset_time]
    else:
        _max_time = max(_conf.keys())
        return _conf[_max_time]

def get_scene_reset_conf(reset_time):
    _conf =  sysconfig.get('monster_reset', {})
    if not _conf:
        return 0
    if _conf.has_key(reset_time):
        return _conf[reset_time]
    else:
        _max_time = max(_conf.keys())
        return _conf[_max_time]

def get_all_skill_ball():
    return sysconfig.get('skill_ball', {})

def get_all_fellow():
    return sysconfig.get('fellow', {})

def get_character_by_leadid(lead_id):
    ''' get character conf by lead id. lead id=1,2,3,4 '''
    _conf = sysconfig.get('character', {})
    return _conf.get(lead_id, {})

def get_fellow_by_fid(fellow_id):
    _conf = sysconfig.get('fellow', {})
    return _conf.get(fellow_id, {})

def get_fellow_advanced(fellow_id, advanced_level):
    _conf = sysconfig.get('fellow_advanced', {})
    return _conf.get(fellow_id, {}).get(advanced_level, {})

def get_fellow_reborn_conf(quality_level, advanced_count):
    _conf = sysconfig.get('fellow_reborn', {})
    return _conf.get(quality_level, {}).get(advanced_count, {})

def get_roleexp_by_level(level):
    _conf = sysconfig.get('roleexp', {})
    return _conf.get(level, {})

def get_max_role_level():
    _all_lvls = sysconfig.get('roleexp', {}).keys()
    return max(_all_lvls)

def get_item_decomposition(item_type, quality_level):
    ''' get decomposition by item type and quality level '''
    _conf = sysconfig.get('item_decomposition', {})
    return _conf.get(item_type, {}).get(quality_level, [])

def get_item_by_itemid(item_id):
    _conf = sysconfig.get('item', {})
    return _conf.get(item_id, {})

def get_item_exp_by_ids(item_ids):
    _total_exp = 0
    _conf      = sysconfig.get('item', {})
    for item_id in item_ids:
        _item_conf = _conf.get(item_id, {})
        _attributs = _item_conf.get('attributes', [])
        for _attr in _attributs:
            if _attr['AttributeID'] in (ATTRIBUTE_TYPE_HORSE_EXP, ATTRIBUTE_TYPE_BOOKWAR_EXP):
                _total_exp += _attr['Value']
    return _total_exp

def get_expand_bag_by_bagtype(bag_type):
    _conf = sysconfig.get('expand_bag', {})
    return _conf.get(bag_type, [])

def get_vip_conf(vip_level):
    _conf = sysconfig.get('vip', {})
    return _conf.get(vip_level, {})

def get_vip_package(vip_level):
    ''' get vip package by vip level
    '''
    _conf = sysconfig.get('vip_package', {})
    return _conf.get(vip_level, {})

def get_vip_chargelist_conf(vip_level, charge_id):
    '''
    get vip chargelist by charge_id
    '''
    _conf = sysconfig.get('vip_chargelist', {})
    return _conf.get(vip_level, {}).get(charge_id, {})

def get_firstpay_reward():
    ''' get vip firstpay reward 
    '''
    return sysconfig.get('firstpay_reward', {}).values()

def get_equip_strengthen_cost(level, equip_type):
    '''get equip strengthen cost by equip level and equip type.
    '''
    _conf = sysconfig.get('equip_strengthen', {})
    if _conf.has_key(level):
        return _conf[level].get(equip_type, {})
    return {}

def get_equip_crit_conf(vip_level):
    '''get equip crit conf by vip level
    '''
    _conf = sysconfig.get('equip_vipcrit', {})
    return _conf.get(vip_level, {})

def get_equip_refine_consume(refine_type):
    '''get refine consume by refine type.
    '''
    _conf = sysconfig.get('refine_consume', {})
    return _conf.get(refine_type, [])

def get_equip_refine_levels(item_id):
    ''' get all strengthen level by item id
    '''
    _conf = sysconfig.get('refine', {})
    return _conf.get(item_id, {}).keys()

def get_equip_refine_conf(item_id, strengthen_level):
    ''' get refine conf by item id and strengthen level
    '''
    _conf = sysconfig.get('refine', {})
    if _conf.has_key(item_id):
        return _conf[item_id].get(strengthen_level, {})
    return {}

def get_treasure_exp_conf(level):
    ''' get treasure exp cost by treasure level
    '''
    _conf = sysconfig.get('treasure_exp', {})
    return _conf.get(level, {})

def get_treasure_refine_conf(treasure_id, refine_level):
    ''' get refine conf by treasure_id and refine_level
    '''
    _conf = sysconfig.get('treasure_refine', {})
    return _conf.get(treasure_id, {}).get(refine_level, {})

def get_treasure_reborn_conf(quality_level, refine_level):
    _conf = sysconfig.get('treasure_reborn', {})
    return _conf.get(quality_level, {}).get(refine_level, {})

def get_item_shop_conf(shop_item_id):
    ''' get shop item id conf
    '''
    _conf = sysconfig.get('item_shop', {})
    return _conf.get(shop_item_id, {})

def get_fellow_decomposition(quality_level):
    ''' get fellow decomposition by quality level 
    ''' 
    _conf = sysconfig.get('fellow_decomposition', {})
    return _conf.get(quality_level, {})

def get_all_scene_dungeon(scene_id):
    ''' get all dungeon by scene_id
    '''
    _conf = sysconfig.get('scene_dungeon', {})
    return _conf.get(scene_id, {})

def get_scene_dungeon(scene_id, dungeon_id):
    ''' get all dungeon by scene_id
    '''
    _conf = sysconfig.get('scene_dungeon', {})
    return _conf.get(scene_id, {}).get(dungeon_id, {})

def get_all_arena_robot():
    ''' get all arena robot conf
    '''
    _conf = sysconfig.get('arena_robot', {})
    return _conf

def get_arena_robot_rank(rank):
    ''' get the rank of arena robot conf
    '''
    _conf = sysconfig.get('arena_robot', {})
    return _conf.get(rank, {})

def get_total_robot_rank():
    ''' get total robot numbers
    '''
    _conf = sysconfig.get('arena_robot', {})
    return len(_conf)

def get_robot_conf(robot_id):
    ''' get robot by id
    '''
    _conf = sysconfig.get('arena_robot', {})
    return _conf.get(robot_id, None)

def get_arena_rank_award(arena_rank):
    ''' get rank award by rank
    '''
    _conf = sysconfig.get('arena_rank_award', {})
    _last_rank = len(_conf)
    if arena_rank > _last_rank:
        arena_rank = _last_rank
    #if not _conf.has_key( arena_rank ):
    #    arena_rank = len(_conf)

    return _conf.get(arena_rank, {})

def get_arena_exchange(exchange_id):
    ''' get exchange conf by exchange_id
    '''
    _conf = sysconfig.get('arena_exchange', {})
    return _conf.get(exchange_id, {})

def get_lvl_viplvl(conf, level=0, vip_level=0):
    ''' get local role lvl and vip lvl of conf
    '''
    _s_lvl, _s_vip_lvl = 0, 0
    _all_lvls = conf.keys()
    for _lvl in _all_lvls:
        if _s_lvl <= _lvl and _lvl <= level:
            _s_lvl = _lvl

    _all_vip_lvls  = conf.get(_s_lvl, {}).keys()
    for _lvl in _all_vip_lvls:
        if _s_vip_lvl <= _lvl and _lvl <= vip_level:
            _s_vip_lvl = _lvl

    return conf.get(_s_lvl, {}).get(_s_vip_lvl, {})

def get_activity_lottery(level, vip_level):
    ''' get local role lvl and vip lvl of lottery items
    {rolelv:{viplv:{id:dict_data},..},..}
    '''
    _conf = sysconfig.get('activity_lottery', {})
    _oss_conf = sysconfig.get('activity_lottery_oss', {})
    _d_normal = get_lvl_viplvl(_conf, level, vip_level)
    _d_oss = get_lvl_viplvl(_oss_conf, level, vip_level)
    _d = dict(_d_normal.items()+_d_oss.items())
    _data = {}
    for _id, _dict_data in _d.iteritems():
        if int(_dict_data.get("ActiveID", 0)) != 0:
            if check_excite_activity_status(_dict_data.get("ActiveID", 0)):
                _data[_id] = _dict_data
        else:
            _data[_id] = _dict_data
   
    return _data

def get_excite_activity_conf():
    ''' get excite activity conf. sync at any time.
    '''
    return sysconfig.get('excite_activity', {})

def check_excite_activity_status(activity_id):
    ''' check excite activity status by activity_id. return 0-stop 1-open'''
    _dt_now   = datetime.now()
    _all_conf = sysconfig.get('excite_activity', {})
    _activity = _all_conf.get(activity_id, {})
    if not _activity:
        #print 'No activity_id<{0}> info.'.format( activity_id )
        return 0
    if _activity['OpenTime'] > _dt_now or _activity['CloseTime'] <= _dt_now:
        #print 'activity_id<{0}> had over. CloseTime: {1}.'.format( activity_id, _activity['CloseTime'] )
        return 0
    return 1

def get_mystical_shop_conf(level, vip_level):
    ''' get local role lvl and vip lvl of mystical items
    '''
    _conf = sysconfig.get('mystical_shop', {})
    return get_lvl_viplvl(_conf, level, vip_level)

def get_eat_peach_conf():
    ''' get eat peach conf '''
    return sysconfig.get('eat_peach', {})

def get_monthly_card_conf(card_type):
    ''' get monthly card conf by card_type '''
    return sysconfig.get('monthly_card', {}).get(card_type, 0)

def get_function_open_conf(function_id):
    ''' get function_open conf by function_id.'''
    _conf = sysconfig.get('function_open', {})
    return _conf.get(function_id, {})

def get_growth_plan_conf():
    ''' get growth plan conf '''
    return sysconfig.get('growth_plan', {})

def get_vip_welfare_conf(t_type=None):
    ''' get vip welfare conf '''
    if t_type is not None:
        return sysconfig.get('vip_awardlist', {}).get(t_type, None)
    return sysconfig.get('vip_awardlist', {})

def get_chaos_conf(chaos_level):
    ''' get conf of chaos level
    '''
    _conf = sysconfig.get('chaos', {})
    return _conf.get(chaos_level, {})

def get_auto_chaos_conf(golds, stars, cur_level, tar_level):
    ''' get conf of chaos level by auto
    '''
    _conf = sysconfig.get('chaos', {})
    costGold, costStar, upCnt = 0, 0, 0
    roleList = []
    _all = _conf.get(chaos_level, {})
    for i in xrange(cur_level+1, tar_level+1):
        costGold += _all.get('CostGold', 0)
        costStar += _all.get('CostStarNum', 0)
        if golds < costGold or stars< costStar:
            break
        upCnt += 1
        role = _all.get('ChangeRole', 0)
        if role > 0:
            roleList.append(role)
    return costGold, costStar, upCnt, roleList

def get_treasureshard_rate_conf(shard_id):
    ''' get treasureshard rate by shard id
    '''
    _conf = sysconfig.get('treasureshard_rate', {})
    return _conf.get(shard_id, None)

def get_login_package_conf(package_id):
    _conf = sysconfig.get('login_package', {})
    return _conf.get(package_id, {})

def get_max_login_package_id():
    _all_ids = sysconfig.get('login_package', {}).keys()
    _max_id  = max(_all_ids) if _all_ids else 0
    return _max_id

def get_pay_login_package_conf(package_id):
    _conf = sysconfig.get('pay_login_package', {})
    return _conf.get(package_id, {})

def get_max_pay_login_package_id():
    _all_ids = sysconfig.get('pay_login_package', {}).keys()
    _max_id  = max(_all_ids) if _all_ids else 0
    return _max_id

def get_online_package_conf(package_group, package_id):
    _conf = sysconfig.get('online_package', {})
    return _conf.get(package_group, {}).get(package_id, {})

def get_all_online_package_id(package_group):
    _conf = sysconfig.get('online_package', {})
    return _conf.get(package_group, {}).keys()

def get_all_online_group():
    return sysconfig.get('online_package', {}).keys()

def get_level_package_conf(level):
    _conf = sysconfig.get('level_package', {})
    return _conf.get(level, {})

def get_openservice_package_conf(package_id):
    _conf = sysconfig.get('openservice_package', {})
    return _conf.get(package_id, {})

def get_all_openservice_id():
    return sysconfig.get('openservice_package', {}).keys()

def get_random_chest_conf(chest_id):
    _conf = sysconfig.get('random_chest', {})
    return _conf.get(chest_id, {})

def get_climbing_conf(tower_layer):
    _conf = sysconfig.get('climbing_tower', {})
    return _conf.get(tower_layer, {})

def get_all_climbing_layer():
    return sysconfig.get('climbing_tower', {}).keys()

def get_elitescene_conf(elitescene_id):
    _conf = sysconfig.get('elitescene', {})
    return _conf.get(elitescene_id, {})

def get_activescene_conf(activescene_id):
    _conf = sysconfig.get('activescene', {})
    return _conf.get(activescene_id, {})

def get_gold_tree_conf():
    return sysconfig.get('gold_tree', {})

def get_version_conf():
    return sysconfig.get('config_version', [])

def get_all_exchange_limited_conf():
    return sysconfig['exchange_limited']

def get_exchange_limited_conf( exchange_id ):
    return sysconfig['exchange_limited'].get( int( exchange_id ), None )

def get_exchange_refresh_conf(list_type, turn):
    _all = sysconfig.get('exchange_refresh', {})

    _all_turns = _all.get( int( list_type ), None )
    turn = int( turn )
    if _all_turns and len( _all_turns ) > turn:
        return _all_turns[ turn ]
    else:
        log.warn('No exchange refresh config. list_type:{0}, turn:{1}.'.format( list_type, turn ))

def get_limit_fellow_conf():
    _all_conf = sysconfig.get('limit_fellow', {})
    for _conf in _all_conf.itervalues():
        if _conf['IsOpen']:
            return _conf

    return {}

def get_limit_fellow_level():
    return sysconfig.get('limit_fellow_level', {})

def get_limit_fellow_pool_levels():
    '''get all shrine levels of limit fellow pool.
    '''
    _conf = sysconfig.get('limit_fellow_pool', {})
    return _conf.keys()

def get_limit_fellow_pool_conf(level):
    '''get limit fellow pool conf by level.
    '''
    _conf = sysconfig.get('limit_fellow_pool', {})
    return _conf.get(level, {})

def get_limit_fellow_award_conf(activity_id):
    _conf = sysconfig.get('limit_fellow_award', {})
    return _conf.get(activity_id, {})

def get_pay_open_conf():
    data = sysconfig.get('pay_activity_group', {})
    for k, conf in data.iteritems():
        if conf.get('IsOpen',0):
            return conf['GroupID']
    return 0 

def get_pay_activity_conf():
    ''' get all pay_activity award conf '''
    _data = sysconfig.get('pay_activity_oss', {})
    group_id = get_pay_open_conf()
    return _data.get(group_id, {})

def get_pay_activity_award_conf(award_id):
    ''' get pay_activity award conf by award id '''
    _conf = sysconfig.get('pay_activity_oss', {})
    group_id = get_pay_open_conf()
    return _conf.get(group_id, {}).get(award_id, {})

def get_consume_open_conf():
    data = sysconfig.get('consume_activity_group', {})
    for k, conf in data.iteritems():
        if conf.get('IsOpen',0):
            return conf['GroupID']
    return 0 
    
def get_consume_activity_conf():
    ''' get all consume_activity award conf '''
    _data = sysconfig.get('consume_activity_oss', {})
    group_id = get_consume_open_conf()
    return _data.get(group_id, {})

def get_consume_activity_award_conf(award_id):
    ''' get consume_activity award conf by award id '''
    _conf = sysconfig.get('consume_activity_oss', {})
    group_id = get_consume_open_conf()
    return _conf.get(group_id, {}).get(award_id, {})

def get_lucky_turntable_conf():
    ''' get lucky turntable conf '''
    return sysconfig.get('lucky_turntable', {})

def get_atlaslist_category_conf(category_id):
    ''' get category conf bu category_id
    '''
    _conf = sysconfig.get('atlaslist', {})
    return _conf.get(category_id, {})

def get_goodwill_level_conf(level):
    ''' get goodwill level conf by level
    '''
    _conf = sysconfig.get('goodwill_level', {})
    return _conf.get(level, {})

def get_goodwill_achieve_conf():
    ''' get all goodwill achieve conf
    '''
    return sysconfig.get('goodwill_achieve', {})

def get_game_limit_value(limit_id):
    return int(sysconfig.get('game_limit', {}).get(limit_id, 0))

def get_all_daily_quest_conf():
    ''' get all daily quest conf.
    '''
    return sysconfig.get('daily_quest', {})

def get_daily_quest_reward_conf(reward_id):
    ''' get daily quest reward conf by reward_id.
    '''
    _conf = sysconfig.get('daily_quest_reward', {})
    return _conf.get(reward_id, {})

def get_all_daily_quest_reward_conf():
    ''' get all daily quest reward conf.
    '''
    return sysconfig.get('daily_quest_reward', {})

def get_joust_exchange_conf(exchange_id):
    ''' get joust exhcange data by exchange_id
    '''
    _conf = sysconfig.get('joust_exchange', {})
    return _conf.get(exchange_id, {})

def get_joust_buy_count_conf(start_turn, end_turn):
    ''' get total cost from start_turn to end_turn.
    '''
    _conf = sysconfig.get('joust_buy_count', {})

    _need_cost = 0
    for _turn in range(start_turn, end_turn):
        _need_cost += _conf.get(_turn, 0)
    return _need_cost

def get_joust_reward_conf(rank):
    ''' get joust reward conf by rank.
    '''
    _all_conf = sysconfig.get('joust_award', {})
    for _conf in _all_conf.itervalues():
        if rank >= _conf['StartRank'] and rank <= _conf['EndRank']:
            return _conf['AwardList']
        elif rank >= _conf['StartRank'] and 0 == _conf['EndRank']:
            return _conf['AwardList']

    return []
def get_lover_kiss_rate_conf(t_type):
    _conf = sysconfig.get('lover_kiss_rate', {})
    return _conf.get(t_type, [])

def get_lover_kiss_conf(opened_num):
    _conf = sysconfig.get('lover_kiss', {})
    return _conf.get(opened_num, [])

def get_lover_kiss_reward_conf_by_type(reward_type):
    _conf = sysconfig.get('lover_kiss_reward', {})
    return _conf.get(reward_type, [])

def get_jade_cost_conf(jade_level):
    _conf = sysconfig.get('jade_cost', {})
    return _conf.get(jade_level, {})

def get_jade_level_conf(jade_level):
    _conf = sysconfig.get('jade_level', {})
    return _conf.get(jade_level, {})

def get_jade_strengthen_conf(jade_level):
    _conf = sysconfig.get('jade_strengthen', {})
    return _conf.get(jade_level, {})

def get_activity_notice_conf():
    return sysconfig.get('activity_notice', {})

def get_group_buy_conf(buy_type = None):
    _conf = sysconfig.get('group_buy', {})
    if buy_type is not None:
        return _conf.get(buy_type, {})
    return _conf

def get_group_buy_reward_list_conf(buy_type, buy_count):
    _all_conf = sysconfig.get('group_buy_reward_list', {})
    return _all_conf.get((buy_type, buy_count), '')

def get_group_buy_count():
    _all_conf = sysconfig.get('group_buy_reward_list', {})
    _result = []
    for _conf in _all_conf:
        _result.append(_conf[1])
    return _result

def get_grow_server_reward_conf(buy_num=None):
    _data = sysconfig.get('growth_plan_welfare', {})
    return _data.get(buy_num, {})

def get_grow_server_conf():
    return sysconfig.get('growth_plan_welfare', {})

    
def get_package_oss_conf(package_id, package_type):
    _all_conf = sysconfig.get('package_oss', {})
    if _all_conf.has_key(package_id):
        activity_conf = []
        for _conf in _all_conf[package_id][package_type]:
            if _conf['ActivityID'] == 0:
                activity_conf.append( _conf )
                continue
            if check_excite_activity_status(_conf['ActivityID']):
                activity_conf.append( _conf )
        return activity_conf
    else:
        return []

def check_item_id_and_type(item_id, item_type):
    _conf = sysconfig.get('item', {})
    _type = _conf.get(int(item_id), {}).get('ItemType', 0)
    return _type == int(item_type)

def get_open_server_quest_conf(acType=None, ids = None):
    _conf = sysconfig.get('open_server_activity', {})
    if ids is None and acType is None:
        return _conf
    elif ids is None:
        return _conf.get(acType, {})
    return _conf.get(acType, {}).get(ids, {})

def get_open_server_shop_conf(quest_id = None):
    _conf = sysconfig.get('open_server_activity_shop', {})
    if quest_id is None:
        return _conf
    return _conf.get(quest_id, {})

def get_all_achievement_conf():
    return sysconfig.get('achievement', {})

def get_new_msg_conf(t_type):
    return sysconfig.get('new_broad_msg', {}).get(t_type, [])
