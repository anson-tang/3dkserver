#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2012 Don.Li
# Summary: 

import MySQLdb
from os.path      import dirname, normpath
from log          import log
from utils        import split_items

import traceback

from constant import *

def monster_data_handler(table, fields, dataset):
    '''
    data format: {DungeonID: {Diff: {dict_data}, ...}, ...}
    其中dict_data= {MonsterID:*, attributes:[{att_data}, ...]}
    '''
    _fields = 'MonsterID', 'Soul', 'Money'
    data = {}

    for row in dataset:
        row_of_dungeon = data.setdefault(row[1], {})
        monster = row_of_dungeon.get(row[2], None)
        if not monster:
            monster = dict(zip(_fields, (row[0], ) + row[3:5]))
            row_of_dungeon[row[2]] = monster
            monster['attributes']  = []

        i = len(fields) + 2

        if row[i]: 
            attr = {'MonsterList':row[i], 'AttributeList':row[i+1], 'OrderNum':row[i+2], 'IsBoss':row[i+3], 'Path':row[i+4], 'BGMusic':row[i+5], }
            if attr not in monster['attributes']:
                monster['attributes'].append( attr )

    return data

def monster_data_handler_old(table, fields, dataset):
    data = {}

    for row in dataset:
        monster = data.get(row[0], None)
        if not monster:
            monster = {}
            i = 0

            for field in fields:
                monster[field] = row[i]
                i += 1

            monster['attributes']  = []

            i += 2

            data[row[0]] = monster
        else:
            i = len(fields) + 2

        if row[i]: 
            attr = {'MonsterList':row[i], 'AttributeList':row[i+1], 'OrderNum':row[i+2], 'Path':row[i+3]}
            if attr not in monster['attributes']:
                monster['attributes'].append( attr )

    return data
def monster_reset_data_handler(table, fields, dataset):
    return {_time: _cost for _time, _cost in dataset}

def scene_sweep_cost_data_handler(table, fields, dataset):
    return {_time: _cost for _time, _cost in dataset}

def item_data_handler(table, fields, dataset):
    data = {}

    for row in dataset:
        item = data.get(row[0], None)
        if not item:
            item = {}
            i = 0

            for field in fields:
                # 特殊格式特别处理('item_type:item_id:teim_num')
                if ('ChangeList' == field):
                    if ('0' == row[i]):
                        item[field] = []
                    else:
                        #cl = row[i].split(':')
                        #item[field] = map(int, cl) if (len(cl) == 3) else []
                        item[field] = split_items( row[i] )
                    i += 1
                    continue
                item[field] = row[i]
                i += 1

            item['attributes']  = []
            #item['changeitems'] = []
            item['treasure_unlock']  = []

            data[row[0]] = item
        else:
            i = len(fields)

        i += 1
        if row[i]:
            attribute = {'AttributeID':row[i], 'Value':row[i+1], 'AddValue':row[i+2]}
            if attribute not in item['attributes']:
                item['attributes'].append( attribute )

        i += 4
        if row[i]:
            treasure_unlock = {'TreasureLevel':row[i], 'AttributeID':row[i+1], 'AttributeValue':row[i+2]}
            if treasure_unlock not in item['treasure_unlock']:
                item['treasure_unlock'].append( treasure_unlock )

    return data

def item_decomposition_data_handler(table, fields, dataset):
    ''' data format: {ItemType: {QualityLevel: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _type, _qlevel = row[0:2]
        if _data.has_key( _type ):
            _type_data = _data[_type]
        else:
            _type_data   = {}
            _data[_type] = _type_data
        if _type_data.has_key( _qlevel ):
            _qlevel_data  = _type_data[_qlevel]
        else:
            _qlevel_data  = []
            _type_data[_qlevel] = _qlevel_data

        _decomposition = dict(zip(fields, row))
        if _decomposition not in _qlevel_data:
            _qlevel_data.append( _decomposition )

    return _data

def random_chest_data_handler(table, fields, dataset):
    ''' data format: {ChestID: {ID: dict_data, ...}, ...}
    '''
    _data = {}

    for row in dataset:
        _id, _chest_id = row[:2]
        if _data.has_key( _chest_id ):
            _chest = _data[_chest_id]
        else:
            _chest = {}
            _data[_chest_id] = _chest
        
        _random = dict(zip(fields, row))
        _chest[_id] = _random

    return _data

def scene_data_handler(table, fields, dataset):
    data = {}# { TownId : scene, ... }
    #scene: { field : value, ... }

    for row in dataset:
        scene = data.get(row[0], None)
        if not scene:
            scene = {}
            i = 0

            for field in fields:
                scene[field] = row[i]
                i += 1

            scene['dungeons']  = []
            scene['rewards'] = []

            data[row[0]] = scene
        else:
            i = len(fields)

        if row[i]:
            dungeon = {'DungeonID':row[i], 'Turn':row[i+1], 'Name':row[i+2], 'Path':row[i+3], 'PosX':row[i+4], 'PosY':row[i+5],
                    'Type':row[i+6], 'StoryID':row[i+7], 'RushMax':row[i+8], 'DropList':row[i+10], 'AwardList':split_items(row[i+12])}
            if dungeon not in scene['dungeons']:
                scene['dungeons'].append( dungeon )

        i += 14
        if row[i]:
            reward = {'StarCount':row[i], 'Reward':row[i+1]}
            if reward not in scene['rewards']:
                scene['rewards'].append( reward )

    return data

def elitescene_data_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        elitescene = _data.get(row[0], None)
        if not elitescene:
            elitescene = {}
            i = 0

            for field in fields:
                if field == 'RewardList':
                    elitescene[field] = split_items(row[i])
                else:
                    elitescene[field] = row[i]
                i += 1

            elitescene['monster']  = []

            _data[row[0]] = elitescene
        else:
            i = len(fields)

        if row[i]:
            monster = {'EliteSceneID':row[i], 'Turn':row[i+1], 'IsBoss':row[i+2], 'MonsterList':row[i+3], 'MonsterAttrList':row[i+4]}
            if monster not in elitescene['monster']:
                elitescene['monster'].append( monster )

    return _data

def activescene_data_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        activescene = _data.get(row[0], None)
        if not activescene:
            activescene = {}
            i = 0

            for field in fields:
                if row[i] and field == 'OpenTime':
                    v = row[i].strftime("%Y-%m-%d %H:%M:%S")
                    activescene[field] = v
                    i += 1
                elif row[i] and field == 'CloseTime':
                    v = row[i].strftime("%Y-%m-%d %H:%M:%S")
                    activescene[field] = v
                    i += 1
                else:
                    activescene[field] = row[i]
                    i += 1

            activescene['monster']  = []

            _data[row[0]] = activescene
        else:
            i = len(fields)

        if row[i]:
            monster = {'Turn':row[i+1], 'IsBoss':row[i+2], 'MonsterList':row[i+3], 'MonsterAttrList':row[i+4]}
            if monster not in activescene['monster']:
                activescene['monster'].append( monster )

    return _data

def task_data_handler(table, fields, dataset):
    data = {}

    for row in dataset:
        task = data.get(row[0], None)
        if not task:
            task = {}
            i = 0

            for field in fields:
                task[field] = row[i]
                i += 1

            task['dungeons']  = []
            task['dialogues'] = []

            data[row[0]] = task
        else:
            i = len(fields)

        if row[i]:
            dungeon = {'ID':row[i], 'Type':row[i+2], 'Value':row[i+3], 'Turn':row[i+4], 'NPC':row[i+5],
                    'Path':row[i+6], 'ICON':row[i+7], 'Dialogue':row[i+8]}
            if dungeon not in task['dungeons']:
                task['dungeons'].append( dungeon )

        i += 9
        if row[i]:
            dialogue = {'ID':row[i], 'Type':row[i+2], 'Turn':row[i+3], 'NPC':row[i+4],
                    'Path':row[i+5], 'ICON':row[i+6], 'Dialogue':row[i+7]}
            if dialogue not in task['dialogues']:
                task['dialogues'].append( dialogue )

    return data

def randname_data_handler(table, fields, dataset):
    data = [[], [], []]

    for row in dataset:
        _first_name, _male, _famale = row[1:]
        if _first_name:
            data[0].append(_first_name)
        if _male:
            data[1].append(_male)
        if _famale:
            data[2].append(_famale)

    return data

def old_scene_dungeon_data_handler(table, fields, dataset):
    '''
    data format: {DungeonID: }
    '''
    dic_dungeon = {}
    dic_townid__turn_dungeon = {}

    for row in dataset:
        DungeonID = row[0]
        Turn = row[1]
        Type = row[6]
        RushMax = row[8]
        TownID = row[9]
        DropList = row[10]

        d = {}
        d['DungeonID'] = DungeonID
        d['Turn'] = Turn
        d['Type'] = Type
        d['RushMax'] = RushMax
        d['TownID'] = TownID
        d['DropList'] = DropList
        dic_dungeon[DungeonID] = d

        l2_dic_turn_data = None
        if TownID in dic_townid__turn_dungeon:
            l2_dic_turn_data = dic_townid__turn_dungeon[TownID]
        else:
            l2_dic_turn_data = {}
            dic_townid__turn_dungeon[TownID] = l2_dic_turn_data
        l2_dic_turn_data[Turn] = d
    return dic_dungeon, dic_townid__turn_dungeon

def scene_dungeon_data_handler(table, fields, dataset):
    '''
    data format: {scene_id: {dungeon_id: dict_data, ..}, ...}
    '''
    _data = {}
    for row in dataset:
        _scene_id, _dungeon_id = row[0:2]
        if _data.has_key( _scene_id ):
            _scene_data = _data[_scene_id]
        else:
            _scene_data = {}
            _data[_scene_id] = _scene_data

        _dungeon = dict(zip(fields, row))
        _dungeon['AwardList'] = split_items(_dungeon['AwardList'])
        if not _scene_data.has_key( _dungeon_id ):
            _scene_data[_dungeon_id] = _dungeon

    return _data

def star_reward_data_handler(table, fields, dataset):
    '''
    data format: {scene_id: {star_count: reward, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _scene_id, _star_count = row[0:2]
        if _data.has_key( _scene_id ):
            _scene_data = _data[_scene_id]
        else:
            _scene_data = {}
            _data[_scene_id] = _scene_data

        _reward = dict(zip(fields, row))
        if not _scene_data.has_key( _star_count ):
            _scene_data[_star_count] = _reward

    return _data

def cardpool_data_handler(table, fields, dataset):
    '''
    data format: {card_type: {shrine_level: {start_level: {id: dict_data, ...}, ...}, ...}, ...}
    其中dict_data = {ID:*, CardID:*, Level:*, StartLevel:*,...}, start_level是玩家等级
    '''
    _data = {}
    for row in dataset:
        _pool_id, _card_type, _shrine_level, _char_level = row[0:4]
        # 三种类型卡片, 1-绿卡, 2-蓝卡, 3-紫卡
        if _data.has_key(_card_type):
            _shrine_data = _data[_card_type]
        else:
            _shrine_data      = {}
            _data[_card_type] = _shrine_data
        # 不同神坛等级
        if _shrine_data.has_key(_shrine_level):
            _char_level_data = _shrine_data[_shrine_level]
        else:
            _char_level_data = {}
            _shrine_data[_shrine_level] = _char_level_data
        # 不同玩家等级
        if _char_level_data.has_key(_char_level):
            _pool_data = _char_level_data[_char_level]
        else:
            _pool_data = {}
            _char_level_data[_char_level] = _pool_data

        # 最终的抽卡池
        _cardpool = dict(zip(fields, row))
        if not _pool_data.has_key( _pool_id ):
            _pool_data[_pool_id] = _cardpool
        #if _cardpool not in _pool_data:
        #    _pool_data.append( _cardpool )

    return _data

def randcard_level_data_handler(table, fields, dataset):
    '''
    data format: {shrine_level: [shrine_level, GreenCount, BlueCount, PurpleCount], ...}
    '''
    _data = {}
    for row in dataset:
        _shrine_level = row[0]
        if _data.has_key( _shrine_level ):
            continue
        _data[_shrine_level] = row
    
    return _data

def campcard_pool_data_handler(table, fields, dataset):
    '''
    data format: {CampID: {RandTime: {ID: dict_data, ...}, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _id, _camp_id, _rand_time = row[0:3]

        if _data.has_key(_camp_id):
            _camp_data = _data[_camp_id]
        else:
            _camp_data = {}
            _data[_camp_id] = _camp_data

        if _camp_data.has_key(_rand_time):
            _rand_data = _camp_data[_rand_time]
        else:
            _rand_data = {}
            _camp_data[_rand_time] = _rand_data

        _rand_data[_id] = dict(zip(fields, row))

    return _data

def fellow_advanced_data_handler(table, fields, dataset):
    #'ID', 'FellowID', 'AdvancedLevel', 'Gold', 'ItemList', 'Life', 'Attack', 'PhysicsDefense', 'MagicDefense', 'BuffID', 'BuffDescription'
    _data = {}

    for row in dataset:
        _fellow_id, _advanced_level = row[1:3]

        if _data.has_key(_fellow_id):
            _row_with_fellow = _data[_fellow_id]
        else:
            _row_with_fellow = {}
            _data[_fellow_id] = _row_with_fellow

        _row_with_fellow[_advanced_level] = dict(zip(fields, row))

    return _data

def fellow_reborn_data_handler(table, fields, dataset):
    '''
    data format: {QualityLevel: {AdvancedCount: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _qlevel, _ad_count = row[0:2]
        if _data.has_key( _qlevel ):
            _qlevel_data = _data[_qlevel]
        else:
            _qlevel_data   = {}
            _data[_qlevel] = _qlevel_data

        if not _qlevel_data.has_key( _ad_count ):
            _qlevel_data[_ad_count] = dict(zip(fields, row))

    return _data

def effect_data_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        _id, _type = row[0:2]

        if _data.has_key(_id):
            _row_with_id = _data[_id]
        else:
            _row_with_id = [None, None]
            _data[_id] = _row_with_id

        if _type == 1:
            _row_with_id[0] = dict(zip(fields, row))
        else:
            _row_with_id[1] = dict(zip(fields, row))

    return _data

def monster_drop_data_handler(table, fields, dataset):
    '''
    data format: {MonsterID: {Diff: {DropID: dict_data, ...}, ...}, ...}
    其中dict_data = {'DropID:*, MonsterID:*, ItemID:*, ...'}
    '''
    _data = {}
    for row in dataset:
        _drop_id, _monster_id, _diff = row[0:3]
        if _data.has_key( _monster_id ):
            _monster_diff = _data[_monster_id]
        else:
            _monster_diff = {}
            _data[_monster_id] = _monster_diff

        if _monster_diff.has_key( _diff ):
            _monster_drop = _monster_diff[_diff]
        else:
            _monster_drop = {}
            _monster_diff[_diff] = _monster_drop

        _drop = dict(zip(fields, row))
        if not _monster_drop.has_key(_drop_id):
            _monster_drop[_drop_id] = _drop

    return _data

def expand_bag_data_handler(table, fields, dataset):
    '''
    data format: {bag_type: [dict_data, ...], ...}
    其中 dict_data = {'ID':*, 'BagType':*, ...}
    '''
    _data = {}
    for row in dataset:
        _bag_type = row[1]
        if _data.has_key( _bag_type ):
            _expand_bag = _data[ _bag_type ]
        else:
            _expand_bag      = []
            _data[_bag_type] = _expand_bag

        _expand = dict(zip(fields, row))
        if _expand not in _expand_bag:
            _expand_bag.append( _expand )

    return _data

def predestine_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        _fellow_id = row[1]
        if _data.has_key( _fellow_id ):
            _predestine = _data[ _fellow_id ]
        else:
            _predestine       = []
            _data[_fellow_id] = _predestine

        _pred = dict(zip(fields, row))
        if _pred not in _predestine:
            _predestine.append( _pred )

    return _data

def refine_data_handler(table, fields, dataset):
    '''
    data format: {ItemId: {StrengthenLevel: {AttributeID: AttributeMax, ...}, ...}, ...}
    其中list_data = [BasicRefineMin, BasicRefineMax, MiddleRefineMin, MiddleRefineMax, TopRefineMin, TopRefineMax, AttributeID, AttributeMax]
    '''
    _data = {}
    for row in dataset:
        _item_id, _s_level = row[0:2]
        _a_id = row[-2]
        if _data.has_key(_item_id):
            _refine_data = _data[_item_id]
        else:
            _refine_data    = {}
            _data[_item_id] = _refine_data

        if _refine_data.has_key(_s_level):
            _strengthen_data = _refine_data[_s_level]
        else:
            _strengthen_data = {}
            _refine_data[_s_level] = _strengthen_data

        if not _strengthen_data.has_key(_a_id):
            _strengthen_data[_a_id] = row[2:]

    return _data

def refine_consume_data_handler(table, fields, dataset):
    '''
    data format: {RefineID: [dict_data, ...], ...}
    其中 dict_data = {'RefineID':*, 'ItemType':*, ...}
    '''
    _data = {}
    for row in dataset:
        _refine_id = row[0]
        if _data.has_key(_refine_id):
            _refine_consume   = _data[_refine_id]
        else:
            _refine_consume   = []
            _data[_refine_id] = _refine_consume

        _consume = dict(zip(fields, row))
        if _consume not in _refine_consume:
            _refine_consume.append( _consume )

    return _data

def chargelist_data_handler(table, fields, dataset):
    '''
    data format: {VipLevel: {ChargeID: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _level, _charge_id = row[0:2]
        if _data.has_key(_level):
            _level_data = _data[_level]
        else:
            _level_data   = {}
            _data[_level] = _level_data
        _charge_data = dict(zip(fields, row))
        if not _level_data.has_key(_charge_id):
            _level_data[_charge_id] = _charge_data

    return _data

def equip_strengthen_data_handler(table, fields, dataset):
    '''
    data format: {StrengthenLevel: {EquipmentType: dict_data, ...}, ...}
    其中dict_data = {'StrengthenLevel':*, 'EquipmentType':*, ...}
    '''
    _data = {}
    for row in dataset:
        _level, _equip_type = row[0:2]
        if _data.has_key(_level):
            _equip_strengthen = _data[_level]
        else:
            _equip_strengthen = {}
            _data[_level]     = _equip_strengthen
        _strengthen = dict(zip(fields, row))
        if not _equip_strengthen.has_key(_equip_type):
            _equip_strengthen[_equip_type] = _strengthen

    return _data

def equip_vipcrit_data_handler(table, fields, dataset):
    '''
    data format: {VipLevel: [OneCrit, TwoCrit, ThreeCrit, FourCrit, FiveCrit]}
    '''
    _data = {}
    for row in dataset:
        _vip_level = row[0]
        if not _data.has_key( _vip_level ):
            _data[_vip_level] = row

    return _data

def treasure_predestine_data_handler(table, fields, dataset):
    '''
    data format: {TreasureID: {FellowID: dict_data, ...}, ...}
    其中dict_data = {'TreasureID':*, 'TreasureName':*, 'FellowID':*, ...}
    '''
    _data = {}
    for row in dataset:
        _treasure_id, _name, _fellow_id = row[0:3]
        if _data.has_key(_treasure_id):
            _fellow_data = _data[_treasure_id]
        else:
            _fellow_data = {}
            _data[_treasure_id] = _fellow_data

        _predestine = dict(zip(fields, row))
        if not _fellow_data.has_key(_fellow_id):
            _fellow_data[_fellow_id] = _predestine

    return _data

def treasure_refine_data_handler(table, fields, dataset):
    '''
    data format: {TreasureID: {RefineLevel: dict_data, ...}, ...}
    其中dict_data = {'TreasureID':*, 'RefineLevel':*, 'CostItemList':*, ...}
    '''
    _data = {}
    for row in dataset:
        _treasure_id, _level = row[0:2]
        if _data.has_key(_treasure_id):
            _level_data = _data[_treasure_id]
        else:
            _level_data = {}
            _data[_treasure_id] = _level_data

        _refine = dict(zip(fields, row))
        if not _level_data.has_key(_level):
            _level_data[_level] = _refine

    return _data

def treasure_reborn_data_handler(table, fields, dataset):
    '''
    data format: {QualityLevel: {RefineLevel: dict_data, ...}, ...}
    其中dict_data = {'QualityLevel':*, 'RefineLevel':*, 'Cost':*}
    '''
    _data = {}
    for row in dataset:
        _qlevel, _rlevel = row[0:2]
        if _data.has_key( _qlevel ):
            _qlevel_data = _data[ _qlevel ]
        else:
            _qlevel_data   = {}
            _data[_qlevel] = _qlevel_data

        _reborn = dict(zip(fields, row))
        if not _qlevel_data.has_key( _rlevel ):
            _qlevel_data[_rlevel] = _reborn

    return _data

def client_dialogue_data_handler(table, fields, dataset):
    '''
    data format: {SceneID: {DialogueGroup: [dict_data, ...], ...}, ...}
    其中dict_data = {'DialogueGroup':*, 'DialogueID':*, 'DialogueType':*, ...}
    '''
    _content_fields = 'DialogueID', 'DialogueTurn', 'NPC', 'NPCName', 'NPCPosition', 'NPCIcon', 'IconPositionX', 'IconPositionY', 'DialogueContent', 'IsChangeScene', 'IsChangeMusic', 'ChangeBattleArrayType', 'MonsterID', 'MonsterAttributeID', 'IsVictory'
    _data = {}
    for row in dataset:
        _scene_id, _group, _dialogue_id = row[3], row[0], row[1]
        if _data.has_key( _scene_id ):
            _scene_data = _data[_scene_id]
        else:
            _scene_data      = {}
            _data[_scene_id] = _scene_data

        if _scene_data.has_key( _group ):
            _dungeon_data = _scene_data[_group]
        else:
            _dungeon_data = []
            _scene_data[_group] = _dungeon_data

        i = len(fields)
        _dialogue = dict(zip(fields, row[:i]))
        for _old_dialogue in _dungeon_data:
            if _old_dialogue['DialogueID'] == _dialogue_id:
                _content_data = _old_dialogue['content']
                break
        else:
            if not _dialogue.has_key( 'content' ):
                _content_data = []
                _dialogue['content'] = _content_data
            _dungeon_data.append( _dialogue )

        if row[i+1]:
            _content  = dict(zip(_content_fields, row[i:]))
            if _content not in _content_data:
                _content_data.append(_content)

    return _data

def dialogue_data_handler(table, fields, dataset):
    '''
    data format: {SceneID: {DialogueGroup: [DialogueID, ...], ...}, ...}
    '''
    _data = {}
    for _scene_id, _group_id, _dialogue_id in dataset:
        if _data.has_key( _scene_id ):
            _scene_data = _data[_scene_id]
        else:
            _scene_data      = {}
            _data[_scene_id] = _scene_data

        if _scene_data.has_key( _group_id ):
            _group_data = _scene_data[_group_id]
        else:
            _group_data = []
            _scene_data[_group_id] = _group_data

        if _dialogue_id not in _group_data:
            _group_data.append( _dialogue_id )

    return _data

def monthly_card_data_handler(table, fields, dataset):
    '''
    format: {id:num, ...}
    '''
    _data = {}
    for row in dataset:
        _data[row[0]] = row[1]
    return _data

def climbing_tower_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        climbing = {}
        i = 0
        for field in fields:
            if field == 'BonusList':
                climbing[field] = split_items(row[i])
            else:
                climbing[field] = row[i]
            i += 1

        _data[row[0]] = climbing

    return _data

def activity_lottery_data_handler(table, fields, dataset):
    '''
    data format: {RoleLevel: {VipLevel: {ID: dict_data, ...}, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _id, _rlevel, _vip_level = row[0:3]
        if _data.has_key( _rlevel ):
            _rlevel_data = _data[_rlevel]
        else:
            _rlevel_data   = {}
            _data[_rlevel] = _rlevel_data

        if _rlevel_data.has_key( _vip_level ):
            _vip_level_data = _rlevel_data[_vip_level]
        else:
            _vip_level_data = {}
            _rlevel_data[_vip_level] = _vip_level_data

        _lottery = dict(zip(fields, row))
        if not _vip_level_data.has_key( _id ):
            _vip_level_data[_id] = _lottery
 
    return _data

def mystical_shop_data_handler(table, fields, dataset):
    '''
    data format: {RoleLevel: {VipLevel: {ID: dict_data, ...}, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _id, _rlevel, _vip_level = row[0:3]
        if _data.has_key( _rlevel ):
            _rlevel_data = _data[_rlevel]
        else:
            _rlevel_data   = {}
            _data[_rlevel] = _rlevel_data

        if _rlevel_data.has_key( _vip_level ):
            _vip_level_data = _rlevel_data[_vip_level]
        else:
            _vip_level_data = {}
            _rlevel_data[_vip_level] = _vip_level_data

        _item = dict(zip(fields, row))
        if not _vip_level_data.has_key( _id ):
            _vip_level_data[_id] = _item
 
    return _data

def login_package_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        row = list(row)
        row[1] = split_items( row[1] )
        _package = dict(zip(fields, row))

        _data[row[0]] = _package

    return _data

def pay_login_package_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        _package = dict(zip(fields, row))
        _package['RewardList'] = split_items(_package['RewardList'])

        _data[row[0]] = _package

    return _data

def online_package_data_handler(table, fields, dataset):
    ''' data format: {group: {ID: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        row = list(row)
        row[3] = split_items( row[3] )
        if _data.has_key( row[0] ):
            _group = _data[row[0]]
        else:
            _group = {}
            _data[row[0]] = _group

        _package = dict(zip(fields, row))
        _group[row[1]] = _package

    return _data

def level_package_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        row = list(row)
        row[1] = split_items( row[1] )
        _package = dict(zip(fields, row))

        _data[row[0]] = _package

    return _data

def openservice_package_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        row = list(row)
        row[1] = split_items( row[1] )
        _package = dict(zip(fields, row))

        _data[row[0]] = _package

    return _data

def newbieguide_data_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        newbieguide = _data.get(row[0], None)
        if not newbieguide:
            newbieguide = {}
            i = 0

            for field in fields:
                newbieguide[field] = row[i]
                i += 1

            newbieguide['content']  = []

            _data[row[0]] = newbieguide
        else:
            i = len(fields)

        if row[i]:
            content_field = 'Turn', 'NPCBust', 'Tips', 'NPCPosition', 'SignPosition', 'GotoType', 'PageID', 'BtnName', 'SceneID', 'PositionX', 'PositionY', 'Wide', 'High', 'IsMark', 'Dubbing'
            content = dict(zip(content_field, row[i+1:]))
            if content not in newbieguide['content']:
                newbieguide['content'].append( content )

    return _data

def constellation_reward_handler(table, fields, dataset):
    return dataset

def constellation_reward_rand_handler(table, fields, dataset):
    data   = {}
    weight = {}

    for row in dataset:
        turn    = data.setdefault(row[1], [])
        turn.append(row[2:])

        weight.setdefault(row[1], 0)
        weight[row[1]] += row[5]

    return data, weight

def gold_tree_data_handler(table, fields, dataset):
    return dataset

def guild_sacrifice_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        if _data.has_key(row[0]):
            continue
        _data[row[0]] = split_items( row[1] )

    return _data

#def guild_shop_limit_data_handler(table, fields, dataset):
#    ''' data format: {guild_level: {_id: dict_data, ...}, ...} '''
#    _data = {}
#
#    for row in dataset:
#        _id, _guild_level = row[0], row[1]
#        if _data.has_key( _guild_level ):
#            _level_data = _data[_guild_level]
#        else:
#            _level_data = {}
#            _data[_guild_level] = _level_data
#
#        _level_data[_id] = dict(zip(fields, row))
#
#    return _data

def guild_shop_item_data_handler(table, fields, dataset):
    ''' data format: {guild_level: {_id: dict_data, ...}, ...} '''
    _data = {}

    for row in dataset:
        _id, _guild_level = row[0], row[1]
        if _data.has_key( _guild_level ):
            _level_data = _data[_guild_level]
        else:
            _level_data = {}
            _data[_guild_level] = _level_data

        _level_data[_id] = dict(zip(fields, row))

    return _data

def guild_contribution_data_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        _contribute = dict(zip(fields, row))
        _contribute['GuildAward'] = split_items( _contribute['GuildAward'] )
        _contribute['PersonAward'] = split_items( _contribute['PersonAward'] )
        _data[row[0]] = _contribute

    return _data

def config_version_data_handler(table, fields, dataset):
    return dataset[0] if dataset else [1,1,1,1]

def exchange_refresh_handler(table, fields, dataset):
    #'RefreshID', 'ListType', 'Turn', 'ItemType', 'ItemID', 'ItemNum', 'Rate', 'AddRate', 'MaxRate'
    _data = {}

    for row in dataset:
        _list_type = _data.setdefault(row[1], [ [], [], [], [] ])

        _turn = row[2] - 1
        _list_type[ _turn ].append( row )

    return _data

def limit_fellow_data_handler(table, fields, dataset):
    '''
    data format: {ID: {ActivityID: *, Awarddesc: data, ...}}
    '''
    i = len(fields)
    _data = {}
    for row in dataset:
        _a_id = row[0]
        if _data.has_key( _a_id ):
            _a_data = _data[_a_id]
        else:
            _a_data = dict(zip(fields, row[:i]))
            _data[_a_id] = _a_data

        _desc_data = _a_data.setdefault('Awarddesc', [])
        _desc_data.append(row[i+1:])

    return _data

def limit_fellow_pool_data_handler(table, fields, dataset):
    '''
    data format: {Level: {id: dict_data, ...}, ...}
    其中dict_data = {ID:*, Rate:*, ...}
    '''
    _data = {}
    for row in dataset:
        _id, _level = row[0], row[1]
        if _data.has_key( _level ):
            _level_data = _data[_level]
        else:
            _level_data = {}
            _data[_level] = _level_data

        _pool_data = dict(zip(fields, row))
        _level_data[_id] = _pool_data

    return _data

def limit_fellow_award_data_handler(table, fields, dataset):
    '''
    data format: {ActivityID: {Rank: dict_data}}}
    '''
    _data = {}
    for row in dataset:
        _a_id, _rank = row[1], row[2]
        if _data.has_key( _a_id ):
            _rank_data = _data[_a_id]
        else:
            _rank_data   = {}
            _data[_a_id] = _rank_data

        _award_data = dict(zip(fields, row))
        _award_data['AwardList'] = split_items( row[3] )

        _rank_data[_rank] = _award_data

    return _data

def pay_activity_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        if not _data.has_key(row[3]):
            _data[row[3]] = {}
        _data[row[3]][row[0]] = dict(zip(fields[:2], row[:2]))
        _data[row[3]][row[0]]['AwardList'] = split_items( row[2] )

    return _data

def consume_activity_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        if not _data.has_key(row[3]):
            _data[row[3]] = {}
        _data[row[3]][row[0]] = dict(zip(fields[:2], row[:2]))
        _data[row[3]][row[0]]['AwardList'] = split_items( row[2] )

    return _data

def lucky_turntable_data_handler(table, fields, dataset):
    '''
    data format: {TurntableType: dict_data, ...}
    其中dict_data = {TurntableType: 1, TotalPay: 6, ItemList: [[1, 1, 100], ...]}
    '''
    i = len(fields)
    _data = {}
    for row in dataset:
        _type = row[0]
        if _data.has_key( _type ):
            _l_data = _data[_type]
        else:
            _l_data = dict(zip(fields, row[:i]))
            _data[_type] = _l_data

        _items = _l_data.setdefault('ItemList', [])
        _items.append(row[i+2:])

    return _data

def atlaslist_data_handler(table, fields, dataset):
    '''
    the third layer change "StarLevel" to "Quality", 2015.03.11
    data format: {CategoryID: {SecondType: {Quality: {Items: [dict_data, ...], Awardlist: award_data}, ...}, ...}, ...}
    '''
    _data = {}
    i = len(fields)
    for row in dataset:
        _category_id, _second_type, _quality = row[1], row[2], row[8]
        if _data.has_key( _category_id ):
            _category_data = _data[_category_id]
        else:
            _category_data = {}
            _data[_category_id] = _category_data

        if _category_data.has_key( _second_type ):
            _second_data = _category_data[_second_type]
        else:
            _second_data = {}
            _category_data[_second_type] = _second_data

        if _second_data.has_key( _quality ):
            _star_data = _second_data[_quality]
        else:
            _star_data = {'Items': []}
            _awardlist = row[i+4]
            _star_data['Awardlist']   = split_items(_awardlist)
            _second_data[_quality] = _star_data

        _dict_data = dict(zip(fields, row[:i]))

        if _dict_data not in _star_data['Items']:
            _star_data['Items'].append(_dict_data)

    return _data

def goodwill_attribute_data_handler(table, fields, dataset):
    '''
    data format: {FellowType: {Level: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _type, _level = row[1], row[2]
        if _data.has_key( _type ):
            _type_data = _data[_type]
        else:
            _type_data = {}
            _data[_type] = _type_data

        if _type_data.has_key( _level ):
            continue
        _dict_data = dict(zip(fields, row))
        _type_data[_level] = _dict_data

    return _data

def game_limit_data_handler(table, fields, dataset):
    '''
    data format: {LimitID:LimitValue, ...}
    '''
    return {_id: _value for _id, _value in dataset}

def daily_quest_reward_data_handler(table, fields, dataset):

    _data = {}

    for row in dataset:
        _reward = dict(zip(fields, row))
        _reward['Reward'] = split_items( _reward['Reward'] )
        _data[row[0]] = _reward

    return _data

def joust_award_data_handler(table, fields, dataset):

    _data = {}
    
    for row in dataset:
        _award = dict(zip(fields, row))
        _award['AwardList'] = split_items( _award['AwardList'] )
        _data[row[0]] = _award

    return _data

def joust_buy_count_data_handler(table, fields, dataset):
    '''
    data format: {Turn:Cost, ...}
    '''
    return {_turn:_cost for _turn, _cost in dataset}

def worldboss_reward_data_handler(table, fields, dataset):
    _data = {}
    
    for row in dataset:
        _award = dict(zip(fields, row))
        _award['RandomItem'] = split_items( _award['RandomItem'] )
        _data[row[0]] = _award

    return _data

def lover_kiss_reward_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        conf_with_type = _data.setdefault(row[1], [])
        conf_with_type.append(row)

    return _data

def rand_package_data_handler(table, fields, dataset):
    '''
    data format: {PackageID: [[dict_data, ...], [...], [...]], ...}
    '''
    _data = {}

    for row in dataset:
        conf_with_type = _data.setdefault(row[1], [[], [], []])
        _package_type = row[2]
        conf_with_type[_package_type].append(dict(zip(fields, row)))

    return _data

def package_count_data_handler(table, fields, dataset):
    '''
    data format: {PackageID: {ActivityID: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        activity_data = _data.setdefault(row[0], {})
        activity_data[row[1]] = dict(zip(fields, row))
        _data[row[0]] = activity_data

    return _data

def happynewyear_data_handler(table, fields, dataset):
    return [_data[1:] for _data in dataset]

def jade_level_data_handler(table, fields, dataset):
    '''
    data format: {JadeLevel: {TargetLevel: dict_data, ...}, ...}
    '''
    _data = {}
    for row in dataset:
        _level, _target_level = row[1], row[2]
        if _data.has_key( _level ):
            _level_data = _data[_level]
        else:
            _level_data = {}
            _data[_level] = _level_data

        _level_data[_target_level] = dict(zip(fields, row))
 
    return _data

def jade_show_data_handler(table, fields, dataset):
    '''
    data format: {JadeLevel: [[ItemType, ItemID, ItemNum], ...], ...}
    '''
    _data = {}
    for row in dataset:
        _level, _item = row[1], row[2:]
        if _data.has_key(_level):
            _level_data = _data[_level]
        else:
            _level_data = []
            _data[_level] = _level_data

        _level_data.append( _item )

    return _data

def group_buy_reward_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        _data[(row[1],row[2])] = row[3]

    return _data
  

def open_server_client_data_handler(table, fields, dataset):
    _data = {}
    award = {}
    for row in dataset:
        row = list(row)
        row[7] = split_items(row[7])
        if _data.has_key(row[1]):
            if _data[row[1]].has_key(row[2]):
                _data[row[1]][row[2]].append(dict(zip(fields, row)))
            else:
                _data[row[1]][row[2]] = [dict(zip(fields, row))]
        else:
            _data[row[1]] = {row[2]:[dict(zip(fields, row))]}

    return _data

def open_server_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        row = list(row)
        row[3] = split_items(row[3])
        if _data.has_key(row[1]):
            _data[row[1]][row[0]] = [row[2], row[3]]
        else:
            _data[row[1]] = {row[0]: [row[2], row[3]]}
    return _data

def open_server_shop_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        _data[row[0]] = dict(zip(fields, row))

    return _data

def achievement_client_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        row = list(row)
        row[5] = split_items(row[5])
        _data[row[0]] = dict(zip(fields, row))

    return _data

def achievement_server_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        row = list(row)
        row[4] = split_items(row[4])
        if _data.has_key(row[1]):
            _data[row[1]][row[0]] = [row[2], row[3], row[4]]
        else:
            _data[row[1]] = {row[0]: [row[2], row[3], row[4]]}
    return _data

def new_broad_server_data_handler(table, fields, dataset):
    _data = {}

    for row in dataset:
        row = list(row)
        _data[row[0]] = row[1:]

    return _data

TABLES = (
        (FOR_ALL, 'attribute', 
            ('AttributeID', 'MonsterLevel', 'MCurrentLife', 'MMaxLife', 'MCurrentMana', 'MMaxMana', 'Attack', 'PhysicsDefense', 'MagicDefense'), None, None),
        (FOR_CLIENT_ONLY, 'attribute_list', ('AttributeID', 'AttributeType', 'Name'), None, None),
        (FOR_ALL, 'character',
            ('CharacterID', 'CharacterDesc', 'NameX', 'NameY', 'Star', 'Quality', 'QualityLevel', 'AdvancedCount', \
                    'ResGroup', 'Path', 'IconPath', 'BustPath', 'AttackID', 'AttackName', 'AttackDesc', 'SkillID', \
                    'SkillName', 'SkillDesc', 'IdleSound', 'AttackSound', 'SkillSound', 'HurtSound', 'Physical', 'Magic', 'MCurrentLife', 'MMaxLife', \
                    'IncreasedLife', 'MCurrentMana', 'AttackType', 'Attack', 'IncreasedAttack', \
                    'PhysicsDefense', 'IncreasedPhysicsDefense', 'MagicDefense', 'IncreasedMagicDefense', \
                    'Crit', 'CritResistance', 'CritDamage', 'CritDamageReduction', 'Block', 'BlockResistance', \
                    'Counter', 'CounterResistance', 'Accurate', 'Miss'), None, None),
        (FOR_ALL, 'monster', ('MonsterID', 'DungeonID', 'Diff', 'Soul', 'Money'), 
            '''SELECT * FROM tb_monster main LEFT JOIN tb_monster_attribute attr ON attr.MonsterID=main.MonsterID''', 
            monster_data_handler),
        (FOR_CLIENT_ONLY, 'monster_skill',
            ('ID', 'BeMove', 'IsTargetBlock', 'IsTargetMiss', 'IsTargetCounter', 'HitArea', 'BonusDamage', 'Target', 'Sound', 'BeHitTime', 'Buffid', 'FloadWord'),
            None, None),
        (FOR_CLIENT_ONLY, 'monster_value' , ('MonsterID', 'MName', 'NameX', 'NameY', 'Scale', 'ResGroup', 'Path', 'Icon', \
                'Camp', 'IsBoss', 'Quality', 'Attack', 'Skill', 'SkillName', 'HurtTime', 'IdleSound', 'AttackSound', 'SkillSound', 'HurtSound', \
                'AttackType', 'Crit', 'CritResistance', 'CritDamage', 'CritDamageReduction', 'Block', 'BlockResistance', \
                'Counter', 'CounterResistance', 'Accurate', 'Miss', 'IsSingle'),
            None, None),
        (FOR_ALL, 'monster_reset', ('ResetTime', 'ResetCost'), None, monster_reset_data_handler),
        (FOR_CLIENT_ONLY, 'floadword' , ('FlowdWordID', 'Bottom', 'Icon', 'Word'), None, None),
        (FOR_ALL, 'item_decomposition' , ('ItemType', 'QualityLevel', 'ItemList'), None, item_decomposition_data_handler), 
        (FOR_ALL, 'scene', ('TownID', 'Name', 'AssectPath', 'Path', 'BGMusic', 'LowLevel', 'PreposeScene', 'StarNum', 'SceneDiff'),
            '''SELECT * FROM tb_scene main LEFT JOIN tb_scene_dungeon dungeon ON dungeon.TownID=main.TownID
            LEFT JOIN tb_scene_star_reward reward ON reward.TownID=main.TownID''', 
            scene_data_handler),
        (FOR_ALL, 'scene_sweep_cost', ('ResetTime', 'ResetCost'), None, scene_sweep_cost_data_handler),
        (FOR_CLIENT_ONLY, 'elitescene', ('SceneID', 'EliteSceneID', 'PrepEliteSceneID', 'EliteSceneName', 'MonsterIcon', 'EliteSceneBG', 'FightBG', 'BGMusic', 'NeedRoleLevel', 'Gold', 'Soul', 'RewardList'),
            '''SELECT * FROM tb_elitescene main 
            LEFT JOIN tb_elitescene_monster monster ON monster.EliteSceneID=main.EliteSceneID''', 
            elitescene_data_handler),
        (FOR_SERVER_ONLY, 'elitescene', ('EliteSceneID', 'SceneID', 'PrepEliteSceneID', 'NeedRoleLevel', 'Gold', 'Soul'), None, None),
        (FOR_CLIENT_ONLY, 'activescene', ('ActiveSceneID', 'ActiveSceneName', 'ActiveSceneBG', 'FightBG', 'BGMusic', 'NeedRoleLevel', 'OpenCycle', 'OpenTime', 'CloseTime', 'CleanNum', 'Price'),
            '''SELECT * FROM tb_activescene main 
            LEFT JOIN tb_activescene_monster monster ON monster.ActiveSceneID=main.ActiveSceneID''', 
            activescene_data_handler),
        (FOR_SERVER_ONLY, 'activescene', ('ActiveSceneID', 'NeedRoleLevel', 'OpenCycle', 'OpenTime', 'CloseTime', 'CleanNum', 'Price'), None, None),
        (FOR_ALL, 'item', ('ItemID', 'ItemName', 'Description', 'UseLevel', 'Quality', 'StarLevel', 'QualityLevel', 'ItemType', 'ChangeList', 'IsUsed', 'Path', 'Icon', 'MaxOverlyingCount', 'Location', 'Price'),
            '''SELECT * FROM tb_item main LEFT JOIN tb_item_attribute attribute ON attribute.ItemID=main.ItemID
            LEFT JOIN tb_treasure_unlock treasureunlock ON treasureunlock.TreasureID=main.ItemID''', 
            item_data_handler),
        (FOR_ALL, 'item_shop', ('ID', 'ItemType', 'ItemID', 'ItemNum', 'CostItemType', 'CostItemID', 'CostItemNum', 'CostItemIncrease', 'MaxCost', 'ItemLimitNum', 'ItemIncrease'), None, None),
        (FOR_SERVER_ONLY, 'random_chest', ('ID', 'ChestID', 'Rate', 'AddRate', 'MaxRate', 'ItemType', 'ItemID', 'ItemNum', 'Notice'), None, random_chest_data_handler),
        #(FOR_SERVER_ONLY, 'scene_dungeon', ('DungeonID', 'Turn', 'Name', 'Path', 'PosX', 'PosY', 'Type', 'StoryID', \
        #    'RushMax', 'TownID', 'DropList', 'WorldDropID'), None, old_scene_dungeon_data_handler),
        (FOR_SERVER_ONLY, 'scene_dungeon', ('TownID', 'DungeonID', 'Turn', 'RushMax', 'DropList', 'WorldDropID', 'AwardList'), None, scene_dungeon_data_handler),

        (FOR_SERVER_ONLY, 'scene_star_reward', ('TownID', 'StarCount', 'Reward'), None, star_reward_data_handler),

        #(FOR_CLIENT_ONLY, 'randname' , ('ID', 'FirstName', 'Male', 'Famale'), None, randname_data_handler),
        (FOR_ALL, 'task', ('ID', 'Name', 'PreTask', 'LowerestLevel', 'HighestLevel', 'StartNPCID', 'StartNPCX', 'StartNPCY', 'FinishNPCID', \
        'FinishNPCX', 'FinishNPCY', 'NeedPassDungeon', 'RewardList'),
            '''SELECT * FROM tb_task main LEFT JOIN tb_task_dungeon dungeon ON dungeon.TaskID=main.ID
            LEFT JOIN tb_task_dialogue dialogue ON dialogue.TaskID=main.ID''', 
            task_data_handler),
        (FOR_ALL, 'fellow', ('FellowID', 'Name', 'FellowDesc', 'Scale', 'NameX', 'NameY', 'Star', 'Quality', 'QualityLevel', \
                'FellowType', 'IsSingle', 'Level', 'Exp', 'AdvancedCount', 'ChangeFellow', 'ResGroup', 'Path', 'IconPath', \
                'Camp', 'Priority', 'AttackID', 'AttackName', 'AttackDesc', 'SkillID', 'SkillName', \
                'SkillDesc', 'IdleSound', 'AttackSound', 'SkillSound', 'HurtSound', 'TalkSound', \
                'Physical', 'Magic', 'MCurrentLife', 'MMaxLife', 'IncreasedLife', \
                'MCurrentMana', 'AttackType', 'Attack', 'IncreasedAttack', 'PhysicsDefense', \
                'IncreasedPhysicsDefense', 'MagicDefense', 'IncreasedMagicDefense', 'Crit', \
                'CritResistance', 'CritDamage', 'CritDamageReduction', 'Block', 'BlockResistance', \
                'Counter', 'CounterResistance', 'Accurate', 'Miss'), None, None),
        (FOR_ALL, 'fellow_decomposition', ('QualityLevel', 'ItemList'), None, None),
        (FOR_ALL, 'fellow_reborn', ('QualityLevel', 'AdvancedCount', 'Cost'), None, fellow_reborn_data_handler),
        (FOR_CLIENT_ONLY, 'fellow_preview', ('ID', 'CardType', 'Quality', 'FellowID'), None, None),
        (FOR_SERVER_ONLY, 'cardpool', ('ID', 'CardID', 'Level', 'StartLevel', 'Rate', 'ItemType', \
                'ItemId', 'ItemNum', 'Notice'), None, cardpool_data_handler),
        (FOR_SERVER_ONLY, 'randcard_level', ('Level', 'GreenCount', 'BlueCount', 'PurpleCount'), None, randcard_level_data_handler),
        (FOR_ALL, 'randcard_consume', ('CardID', 'ItemType', 'ItemID', 'ItemNum', 'FreeTime'), None, None),
        (FOR_ALL, 'campcard_cost', ('RandTime', 'RandCost', 'Multiple'), None, None),
        (FOR_SERVER_ONLY, 'campcard_pool', ('ID', 'CampID', 'RandTime', 'Rate', 'ItemType', 'ItemID', 'ItemNum', 'Notice'), None, campcard_pool_data_handler),

        (FOR_ALL, 'roleexp', ('Level', 'RoleExp', 'White', 'Green', 'Blue', 'Purple', 'Orange', 'Red'), None, None),

        (FOR_ALL, 'fellow_advanced', ('ID', 'FellowID', 'AdvancedLevel', 'FellowLevelLimit', 'Gold', 'ItemList', 'Life', 'Attack', 'PhysicsDefense', 'MagicDefense', 'BuffID', 'BuffName', 'BuffDescription'), None,
                fellow_advanced_data_handler),
        #(FOR_ALL, 'skill_ball', ('ball_id', 'item_type', 'item_id', 'item_num', 'price'), None, None),
        (FOR_CLIENT_ONLY, 'effect', ('ID', 'ActionType', 'ActionStartEffect', 'StartDelayTime', 'StartDuration', 'StartSound', 'ActionMovmentEffect', 'MovmentDelayTime', 'MovmentDuration', 'MoveMentSound', 'ActionTargetEffect', 'TargetDelayTime', 'TargetDuration', 'TargetSound'), None,
                effect_data_handler),
        (FOR_SERVER_ONLY, 'monster_drop', ('DropID', 'MonsterID', 'MonsterDiff', 'ItemType', 'ItemID', 'RateStart', 'RateAdd', 'RateMax', 'ItemNum', 'ActiveID'), None, monster_drop_data_handler),
        (FOR_SERVER_ONLY, 'monster_drop_oss', ('DropID', 'MonsterID', 'MonsterDiff', 'ItemType', 'ItemID', 'RateStart', 'RateAdd', 'RateMax', 'ItemNum', 'ActiveID'), None, monster_drop_data_handler),
        (FOR_ALL, 'expand_bag', ('ID', 'BagType', 'BagCount', 'Cost'), None, expand_bag_data_handler),
        (FOR_CLIENT_ONLY, 'predestine', ('ID', 'FellowID', 'Turn', 'PredestineName', 'PredestineDesc', 'ItemType', 'ItemID', 'AttributeList'), None, predestine_data_handler),
        (FOR_CLIENT_ONLY, 'buff', ('BuffID', 'BuffType', 'FloatWord', 'BuffEffect', 'FloatX', 'FloatY', \
                'FloatZ', 'Target', 'BuffArea', 'RoundCount', 'IsActionTakeEffect', 'Probability', 'BuffAttribute', 'BuffAttributeValue'), None, None),
        (FOR_ALL, 'refine', ('ItemID', 'StrengThenLV', 'BasicRefineMin', 'BasicRefineMax', 'MiddleRefineMin', \
                        'MiddleRefineMax', 'TopRefineMin', 'TopRefineMax', 'AttributeID', 'AttributeMax'), None, refine_data_handler),
        (FOR_ALL, 'refine_consume', ('RefineID', 'ItemType', 'ItemID', 'ItemNum'), None, refine_consume_data_handler),
        (FOR_ALL, 'vip', ('VipLevel', 'Cost', 'StrengthenCrit', 'TowerFightCount', 'TowerResetCount', \
                'TowerBuyReset', 'EliteSceneCount', 'ActiveSceneCount', 'DungeonTime', 'AutoFight', \
                'SceneSkip', 'EliteSceneSkip', 'ActiveSceneSkip', 'TowerSkip', 'AutoWorldBoss', \
                'ContinuousBattles', 'FreeMaxCount', 'BuyMaxCount', 'GuildSacrificeCount', 'SceneALLSweep', \
                'JoustCount', 'FreeDigCount', 'DungeonReset', 'TreasureTenPlunder'), None, None),
        (FOR_ALL, 'vip_chargelist', ('VipLevel', 'ChargeID', 'Cost', 'ChargeType', 'GetCredits', 'GiftCredits', 'FirstGiftCredits', 'CreditsBack', 'StartTime', 'Duration'), None, chargelist_data_handler),
        (FOR_CLIENT_ONLY, 'vip_chargedesc', ('ChargeID', 'ChargeName', 'ChargeDesc'), None, None),
        (FOR_ALL, 'vip_package', ('VipLevel', 'ItemType', 'ItemID', 'OriginalPrice', 'PresentPrice'), None, None),
        (FOR_CLIENT_ONLY, 'vip_desc', ('ID', 'VipLevel', 'VipDesc', 'Sign'), None, None),
        (FOR_CLIENT_ONLY, 'npc', ('NPCID', 'Name', 'NameX', 'NameY', 'Path', 'Bust'), None, None),
        (FOR_ALL, 'equip_strengthen', ('StrengthenLevel', 'EquipmentType', 'WhiteCost', 'GreenCost', 'BlueCost', 'PurpleCost', 'OrangeCost', 'RedCost'), None, equip_strengthen_data_handler),
        (FOR_SERVER_ONLY, 'equip_vipcrit', ('VipLevel', 'OneCrit', 'TwoCrit', 'ThreeCrit', 'FourCrit', 'FiveCrit'), None, equip_vipcrit_data_handler),
        (FOR_CLIENT_ONLY, 'treasure_predestine', ('TreasureID', 'TreasureName', 'FellowID', 'PredestineName', 'PredestineDesc'), None, treasure_predestine_data_handler),
        (FOR_ALL, 'treasure_exp', ('TreasureLevel', 'WhiteCost', 'GreenCost', 'BlueCost', 'PurpleCost', 'OrangeCost'), None, None),
        (FOR_ALL, 'treasure_refine', ('TreasureID', 'RefineLevel', 'CostItemList', 'CostGold', 'AttributeID', 'AttributeValue'), None, treasure_refine_data_handler),
        (FOR_ALL, 'treasure_reborn', ('QualityLevel', 'RefineCount', 'Cost'), None, treasure_reborn_data_handler),
        (FOR_CLIENT_ONLY, 'game_sound', ('SystemKey', 'SoundName'), None, None),
        (FOR_CLIENT_ONLY, 'dialogue', ('DialogueGroup', 'DialogueID', 'DialogueType', 'SceneID', 'DungeonID', 'DungeonDiff', 'MonsterRound', 'MonsterTurn', 'MonsterID', 'Life', 'MonsterDied', 'Win', 'IsMark'), 
            '''SELECT * FROM tb_dialogue main LEFT JOIN tb_dialogue_content content ON content.DialogueID=main.DialogueID''', 
            client_dialogue_data_handler),
        (FOR_SERVER_ONLY, 'dialogue', ('SceneID', 'DialogueGroup', 'DialogueID'), None, dialogue_data_handler),
        (FOR_SERVER_ONLY, 'mystical_shop', ('ID', 'RoleLevel', 'VipLevel', 'ItemType', 'ItemID', 'ItemNum', 'CostItemType', 'CostItemID', 'CostItemNum', 'Rate', 'RateAdd'), None, mystical_shop_data_handler),
        (FOR_ALL, 'firstpay_reward', ('ID', 'ItemType', 'ItemID', 'ItemNum'), None, None),
        (FOR_ALL, 'eat_peach', ('ID', 'StartTime', 'EndTime', 'AddEnergy', 'Rate', 'ItemType', 'ItemID', 'ItemNum', 'Count'), None, None),
        (FOR_ALL, 'growth_plan', ('PlanLevel', 'CreditsNum'), None, None),
        (FOR_ALL, 'growth_plan_welfare', ('BuyNum', 'RewardList'), None, None),
        (FOR_ALL, 'monthly_card', ('ID', 'ItemNum'), None, monthly_card_data_handler),
        (FOR_ALL, 'vip_awardlist', ('VipLevel', 'ItemType', 'ItemID', 'ItemNum', 'OriginalPrice', 'PresentPrice', 'Count'), None, None),
        (FOR_CLIENT_ONLY, 'function_open', ('BtnName', 'ID', 'FunctionName', 'RoleLevel', 'VipLevel', 'SceneID', 'TutorialID', 'IsHidden'), None, None), 
        (FOR_SERVER_ONLY, 'function_open', ('ID', 'RoleLevel'), None, None),
        (FOR_ALL, 'climbing_tower', ('TowerID', 'TowerName', 'MonsterIcon', 'FightBG', 'BGMusic', 'MonsterIcon', 'MonsterList', 'MonsterAttributeID', 'PassType', 'PassValue', 'RewardGold', 'RewardSoul', 'BonusList', 'ResetCost', 'NeedTime', 'MonsterType'), None, climbing_tower_data_handler),
        (FOR_ALL, 'chaos', ('ID', 'Name', 'AttributeID', 'AttributeValue', 'Color', 'CostStarNum', 'CostGold', 'ChangeRole'), None, None),
        (FOR_SERVER_ONLY, 'activity_lottery', ('ID', 'RoleLevel', 'VipLevel', 'ItemType', 'ItemID', 'ItemNum', 'Rate', 'AddRate', 'Notice', 'ActiveID'), None, activity_lottery_data_handler),
        (FOR_SERVER_ONLY, 'activity_lottery_oss', ('ID', 'RoleLevel', 'VipLevel', 'ItemType', 'ItemID', 'ItemNum', 'Rate', 'AddRate', 'Notice', 'ActiveID'), None, activity_lottery_data_handler),
        (FOR_SERVER_ONLY, 'arena_rank_award', ('ArenaRank', 'ArenaRankList'), None, None),
        (FOR_ALL, 'arena_exchange', ('ID', 'ItemType', 'ItemID', 'ItemNum', 'NeedPrestige', 'MaxExchangeCount', 'DailyExchangeCount', 'NeedLevel'), None, None),
        (FOR_SERVER_ONLY, 'arena_robot', ('ID', 'RobotName', 'RobotList', 'RobotLevel'), None, None),
        (FOR_ALL, 'constellation_reward', ('Turn', 'StarNum', 'ItemType', 'ItemID', 'ItemNum'), None, constellation_reward_handler),
        (FOR_SERVER_ONLY, 'constellation_reward_rand', ('ID', 'Turn', 'ItemType', 'ItemID', 'ItemNum', 'Rate'), None, constellation_reward_rand_handler),
        (FOR_ALL, 'constellation_star', ('ExtraTurn', 'ExtraStarNum'), None, None),
        (FOR_ALL, 'treasureshard_rate', ('TreasureshardID', 'Rate', 'AddRate', 'MaxRate'), None, None),
        (FOR_SERVER_ONLY, 'excite_activity', ('ID', 'ActivityID', 'ActivityType', 'ActivityName', 'ActivityIcon', 'IsOpen', 'OpenTime', 'CloseTime'), None, None),
        (FOR_ALL, 'pay_login_package', ('ID', 'RewardList', 'NeedCost'), None, pay_login_package_data_handler),
        (FOR_ALL, 'login_package', ('ID', 'RewardList'), None, login_package_data_handler),
        (FOR_ALL, 'online_package', ('PackageGroup', 'PackageID', 'OnlineTime', 'RewardList'), None, online_package_data_handler),
        (FOR_ALL, 'level_package', ('Level', 'RewardList'), None, level_package_data_handler),
        (FOR_ALL, 'openservice_package', ('ID', 'RewardList'), None, openservice_package_data_handler),
        (FOR_CLIENT_ONLY, 'newbieguide', ('GroupID', 'GuideType', 'UnlockLevel', 'SceneID', 'PreGroupID', 'IsNotice', 'IconPath', 'ToPageID'), 
                '''SELECT * FROM tb_newbieguide main LEFT JOIN tb_newbieguide_list list ON list.GroupID=main.GroupID''', 
                newbieguide_data_handler),
        (FOR_CLIENT_ONLY, 'error_tips', ('ErrorID', 'ErrorKey', 'ErrorType', 'ErrorLink'), None, None),
        (FOR_CLIENT_ONLY, 'exchange_preview', ('previewID', 'ListType', 'ItemType', 'ItemID'), None, None),
        (FOR_SERVER_ONLY, 'exchange_refresh', ('RefreshID', 'ListType', 'Turn', 'ItemType', 'ItemID', 'ItemNum', 'Rate', 'AddRate', 'MaxRate'), None, exchange_refresh_handler),
        (FOR_ALL, 'exchange_limited', ('ExchangeID', 'Title', 'Type', 'ResetCost', 'AddCost', 'MaxCost', 'ExchangeNum', 'MaterialLockedCost', 'TargetLockedCost'), None, None),
        (FOR_SERVER_ONLY, 'config_version', ('SysconfigVer', 'KeywordVer', 'BanWordChat', 'BanWordName'), '''SELECT SysconfigVer,KeywordVer,BanWordChat,BanWordName FROM tb_config_version WHERE ID=1''', config_version_data_handler),
        (FOR_ALL, 'gold_tree', ('Damage', 'GoldReward'), None, gold_tree_data_handler),
        (FOR_CLIENT_ONLY, 'guild_level', ('Level', 'GuildHall', 'GuildDungeon', 'GuildWelfareHall', 'GuildShop', 'GuildTask', 'MembersCount', 'SacrificeNum'), None, None),
        (FOR_CLIENT_ONLY, 'guild_sacrifice', ('Level', 'AwardList'), None, guild_sacrifice_data_handler),
        (FOR_CLIENT_ONLY, 'guild_shop_item', ('ID', 'GuildLevel', 'ItemType', 'ItemID', 'ItemNum', 'Cost', 'BuyMax'), None, None),
        (FOR_CLIENT_ONLY, 'guild_contribution', ('ID', 'Name', 'Icon', 'CostItemType', 'CostItemID', 'CostItemNum', 'GuildAward', 'PersonAward', 'VipLevel'), None, guild_contribution_data_handler),
        (FOR_ALL, 'limit_fellow', ('ActivityID', 'ActivityName', 'IsOpen', 'MonsterList'), 
                ''' SELECT * FROM tb_limit_fellow main LEFT JOIN tb_limit_fellow_desc limit_desc ON limit_desc.ActivityID=main.ActivityID ''',
                #''' SELECT * FROM tb_limit_fellow main LEFT JOIN tb_limit_fellow_desc limit_desc ON limit_desc.ActivityID=main.ActivityID WHERE main.IsOpen=1 ''',
                limit_fellow_data_handler),
        (FOR_SERVER_ONLY, 'limit_fellow_pool', ('ID', 'Level', 'Rate', 'ItemType', 'ItemId', 'ItemNum', 'Notice'), None, limit_fellow_pool_data_handler),
        (FOR_SERVER_ONLY, 'limit_fellow_level', ('Level', 'RandCount'), None, None),
        (FOR_SERVER_ONLY, 'limit_fellow_award', ('ID', 'ActivityID', 'Rank', 'AwardList'), None, limit_fellow_award_data_handler),
        (FOR_SERVER_ONLY, 'pay_activity_oss', ('ID', 'TotalPay', 'AwardList', 'GroupID'), None, pay_activity_data_handler),
        (FOR_SERVER_ONLY, 'pay_activity_group', ('GroupID', 'GroupDesc', 'IsOpen'), None, None),
        (FOR_ALL, 'consume_activity_oss', ('ID', 'TotalConsume', 'AwardList', 'GroupID'), None, consume_activity_data_handler),
        (FOR_ALL, 'consume_activity_group', ('GroupID', 'GroupDesc', 'IsOpen'), None, None),
        (FOR_CLIENT_ONLY, 'lucky_turntable', ('TurntableType', 'TotalPay', 'RewardGolds'),
                ''' SELECT * FROM tb_lucky_turntable main LEFT JOIN tb_lucky_turntable_item item ON item.TurntableType=main.TurntableType ''', 
                lucky_turntable_data_handler),
        (FOR_SERVER_ONLY, 'lucky_turntable', ('TurntableType', 'TotalPay', 'RewardGolds'), None, None),
        (FOR_SERVER_ONLY, 'activity_notice', ('ID', 'Title', 'Content', 'OpenTime', 'CloseTime'), None, None),
        (FOR_ALL, 'atlaslist', ('ID', 'CategoryID', 'SecondType', 'StarLevel', 'ItemType', 'ItemID', 'Name', 'Icon', 'Quality'), 
                ''' SELECT * FROM tb_atlaslist main LEFT JOIN tb_atlaslist_award award ON award.CategoryID=main.CategoryID AND award.SecondType=main.SecondType AND award.Quality=main.Quality ''', 
                atlaslist_data_handler),
        (FOR_ALL, 'goodwill_achieve', ('ID', 'AchieveValue', 'Name', 'IconQuality', 'Icon', 'AttributeID', 'AttributeValue'), None, None),
        (FOR_ALL, 'goodwill_level', ('Level', 'PurpleExp', 'PurpleCrit'), None, None),
        (FOR_ALL, 'worldboss_attribute', ('Level', 'Life', 'MCurrentMana', 'MMaxMana', 'Attack', 'PhysicsDefense', 'MagicDefense', 'Crit', 'Block', 'Counter', 'Accurate', 'Miss'), None, None),
        (FOR_ALL, 'worldboss_reward', ('Rank', 'Gold', 'Prestige', 'RandomItem', 'Rate'), None, worldboss_reward_data_handler),
        (FOR_ALL, 'worldboss_inspire', ('Level', 'GoldRate', 'GoldAddRate', 'GoldCost', 'CreditsRate', 'CreditsAddRate', 'CreditsCost'), None, None),
        (FOR_CLIENT_ONLY, 'goodwill_attribute', ('ID', 'FellowType', 'Level', 'AttributeID', 'AttributeValue'), None, goodwill_attribute_data_handler),
        (FOR_ALL, 'game_limit', ('LimitID', 'LimitValue'), None, game_limit_data_handler),
        (FOR_ALL, 'daily_quest', ('ID', 'Title', 'Description', 'Icon', 'Requirements', 'Score', 'RewardList'), None, None),
        (FOR_ALL, 'daily_quest_reward', ('ID', 'Score', 'Reward'), None, daily_quest_reward_data_handler),
        (FOR_ALL, 'joust_award', ('StartRank', 'EndRank', 'AwardList'), None, joust_award_data_handler),
        (FOR_ALL, 'joust_exchange', ('ExchangeID', 'ItemType', 'ItemID', 'ItemNum', 'NeedHonor', 'MaxExchangeCount', 'WeekExchangeCount', 'DailyExchangeCount', 'NeedLevel'), None, None),
        (FOR_ALL, 'joust_buy_count', ('Turn', 'Cost'), None, joust_buy_count_data_handler),
        (FOR_SERVER_ONLY, 'lover_kiss', ('KissNum', 'LuxuryRewardRate'), None, None),
        (FOR_SERVER_ONLY, 'lover_kiss_rate', ('ID', 'Rate'), None, None),
        (FOR_SERVER_ONLY, 'lover_kiss_reward', ('ID', 'RewardType', 'Rate', 'ItemType', 'ItemID', 'ItemNum', 'Notice'), None, lover_kiss_reward_handler),
        (FOR_CLIENT_ONLY, 'lover_kiss_reward_preview', ('ID', 'ItemType', 'ItemID', 'ItemNum'), None, None),
        (FOR_SERVER_ONLY, 'package', ('ID', 'PackageID', 'PackageType', 'RoleLevel', 'VipLevel', 'Rate', 'ItemType', 'ItemID', 'ItemNum', 'Notice', 'ActivityID'), None, rand_package_data_handler),
        (FOR_SERVER_ONLY, 'package_oss', ('ID', 'PackageID', 'PackageType', 'RoleLevel', 'VipLevel', 'Rate', 'ItemType', 'ItemID', 'ItemNum', 'Notice', 'ActivityID'), None, rand_package_data_handler),
        (FOR_SERVER_ONLY, 'package_count', ('PackageID', 'ActivityID', 'PersonalCount', 'ServerCount'), None, None),
        (FOR_CLIENT_ONLY, 'happynewyear', ('ID', 'ItemType', 'ItemID', 'ItemNum'), None, happynewyear_data_handler),
        (FOR_CLIENT_ONLY, 'tomb_treasure',('ID', 'ItemType', 'ItemID'), None, None),
        (FOR_ALL, 'jade_cost', ('JadeLevel', 'CostItemType', 'CostItemID', 'CostItemNum'), None, None),
        (FOR_SERVER_ONLY, 'jade_level', ('ID', 'JadeLevel', 'TargetLevel', 'Rate', 'ExtraOdds', 'ItemType', 'ItemID', 'ItemNum'), None, jade_level_data_handler),
        (FOR_CLIENT_ONLY, 'jade_show', ('ID', 'JadeLevel', 'ItemType', 'ItemID', 'ItemNum'), None, jade_show_data_handler),
        (FOR_ALL, 'jade_strengthen', ('JadeLevel', 'WhiteExp', 'GreenExp', 'BlueExp', 'PurpleExp', 'OrangeExp'), None, None),
        (FOR_ALL, 'group_buy', ('BuyType', 'ItemType', 'ItemID', 'ItemNum', 'OriginalPrice', 'CurrentPrice', 'LimitNum'), None, None),
        (FOR_SERVER_ONLY, 'group_buy_reward_list', ('ID', 'BuyType', 'BuyCount', 'RewardList'), None, group_buy_reward_data_handler),
        (FOR_CLIENT_ONLY, 'group_buy_reward_list', ('ID', 'BuyType', 'BuyCount', 'RewardList'), None, None),
        (FOR_CLIENT_ONLY, 'open_server_activity', ('ID', 'Day', 'Turn', 'Name', 'ActivityType', 'Value', 'Description', 'RewardList'), None, open_server_client_data_handler),
        (FOR_SERVER_ONLY, 'open_server_activity', ('ID', 'ActivityType', 'Value', 'RewardList'), None, open_server_data_handler),
        (FOR_ALL, 'open_server_activity_shop', ('Day', 'ItemType', 'ItemID', 'ItemNum', 'OriginalPrice', 'PresentPrice', 'ServerCount'), None, open_server_shop_data_handler),
        (FOR_CLIENT_ONLY, 'achievement', ('ID', 'QuestType', 'Value', 'PreviousID', 'Description', 'RewardList', 'Icon', 'Quality', 'RewardDesc', 'IsEnd'), None, achievement_client_data_handler),
        (FOR_SERVER_ONLY, 'achievement', ('ID', 'QuestType', 'Value', 'PreviousID', 'RewardList'), None, achievement_server_data_handler),
        (FOR_SERVER_ONLY, 'new_broad_msg', ('GiftType', 'GiftLevel', 'GiftID', 'GiftNum'), None, new_broad_server_data_handler),
    )



def db_config():
    from setting import DB

    _host = DB['host']
    _port = DB['port']
    _user = DB['user']
    _pass = DB['pass']
    _db   = DB['db_sysconfig']

    return {'host'       : _host, 
            'port'       : _port, 
            'user'       : _user, 
            'passwd'     : _pass, 
            'db'         : _db,
            'charset'    : 'utf8',
            'use_unicode': True
        }

def load_all_config(limit=FOR_ALL):
    conn   = MySQLdb.connect(**db_config())
    SELECT = 'SELECT {0} FROM tb_{1}'
    result = {}
    
    for _limit, table, fields, custom_sql, custom_handler in TABLES:
        if _limit not in (FOR_ALL, limit):
            continue

        cursor = conn.cursor()
        try:
            data = {}

            _sql = custom_sql if custom_sql else SELECT.format(','.join(fields), table)

            cursor.execute(_sql)
            _dataset = cursor.fetchall()

            if custom_handler:
                data = custom_handler(table, fields, _dataset)
            else:
                for row in _dataset:
                    if row:
                        #data[row[0]] = row
                        data[row[0]] = dict(zip(fields, row))

            result[table] = data
        except Exception, e: 
            log.warn('error sql: %s' % _sql) 
            traceback.print_exc()
            continue

        cursor.close()

    conn.close()

    result.update({'constants':constant_data()})  
    return result

def load_all_keyword():
    conn   = MySQLdb.connect(**db_config())
    cursor = conn.cursor()

    result = {}
    fields = 'k', 'v'

    sql    = 'SELECT lang_id FROM tb_lang'
    cursor.execute( sql )
    all_lang = [str(lang_id) for lang_id in cursor.fetchall()]
    all_lang.append('0')

    for lang in all_lang:
        _table_name = 'tb_keyword_%s' % lang if lang != '0' else 'tb_keyword'
        sql         = 'SELECT %s FROM %s' % (','.join(fields), _table_name)
        cursor.execute( sql )

        result[lang] = {k:v for k, v in cursor.fetchall()}

    return result

def load_all_randname():
    conn   = MySQLdb.connect(**db_config())
    cursor = conn.cursor()

    result = {}
    fields = 'ID', 'FirstName', 'Male', 'Famale'

    _table_name = 'tb_randname'
    sql         = 'SELECT %s FROM %s' % (','.join(fields), _table_name)

    cursor.execute( sql )

    _dataset = cursor.fetchall()
    result   = randname_data_handler(_table_name, fields, _dataset)

    return result

def constant_data():
    constant_data = {
            'FELLOWS_LIMIT_WITH_PLAYER_LEVEL': FELLOWS_LIMIT_WITH_PLAYER_LEVEL,
            'JADE_LIMIT_WITH_PLAYER_LEVEL': JADE_LIMIT_WITH_PLAYER_LEVEL,
            'AVOID_WAR_CREDITS': AVOID_WAR_CREDITS,
            'AVOID_USER_TIME_SPLIT': AVOID_USER_TIME_SPLIT,
            'CONSTELLATION_SELECT_MAX': CONSTELLATION_SELECT_MAX,
            'CONSTELLATION_FREE_REFRESH': CONSTELLATION_FREE_REFRESH,
            'CONSTELLATION_CREDITS_FOR_FREE': CONSTELLATION_CREDITS_FOR_FREE,
            'CONSTELLATION_CREDITS_FOR_REWARD': CONSTELLATION_CREDITS_FOR_REWARD,
            'NORMAL_ROSE_MAX_NUM' : NORMAL_ROSE_MAX_NUM,
            'BLUE_ROSE_MAX_NUM' : BLUE_ROSE_MAX_NUM,
            'BATCH_DECOMPOSE_PRICE' : BATCH_DECOMPOSE_PRICE,
            }
    return constant_data

if __name__ == '__main__':
    print db_config()
    sysconfig = load_all_config()
    #print 'sysconfig:', sysconfig

    scene = repr(sysconfig['scene'][101]['Name'])
    print scene
