#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: All Userdb fields
#

TABLE_FIELDS = {
          'character': (( 'id', 'account', 'nick_name', 'lead_id', 'level', 'exp', 'vip_level', 'might', 'recharge', \
                  'golds', 'credits', 'credits_payed', 'total_cost', 'firstpay', 'monthly_card', 'dual_monthly_card', 'growth_plan', 'register_time', \
                  'last_login_time', 'fellow_capacity', 'item_capacity', 'treasure_capacity', 'equip_capacity', \
                  'equipshard_capacity', 'jade_capacity', 'soul', 'hunyu', 'prestige', 'honor', 'energy', \
                  'chaos_level', 'scene_star', 'douzhan', 'tutorial_steps', 'friends', 'charge_ids' ),
                  ('register_time', 'last_login_time')),

             'fellow': (( 'id', 'cid', 'fellow_id', 'level', 'exp', 'advanced_level', 'on_troop', 'is_major', 'camp_id', 'deleted', 'create_time', 'update_time', 'del_time' ), 
                 ('create_time', 'update_time', 'del_time')),

              'scene': (( 'id', 'cid', 'scene_id', 'dungeon_id', 'dungeon_star', 'dungeon_today_count', 'dungeon_award', 'dungeon_last_time' ), 
                  ('dungeon_last_time', )),
  
          'bag_equip': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'camp_id', 'position_id', 'level', 'strengthen_cost', \
                  'refine_cost', 'refine_attribute', 'deleted', 'create_time', 'update_time', 'del_time', 'aux_data' ), 
                  ('create_time', 'update_time', 'del_time')),
  
     'bag_equipshard': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'deleted', 'create_time', 'update_time', 'del_time', 'aux_data' ), 
                  ('create_time', 'update_time', 'del_time')),
 
     'bag_fellowsoul': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'deleted', 'create_time', 'update_time', 'del_time', 'aux_data' ),
                  ('create_time', 'update_time', 'del_time')),
  
           'bag_item': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'deleted', 'create_time', 'update_time', 'del_time', 'aux_data' ),
                  ('create_time', 'update_time', 'del_time')),
  
       'bag_treasure': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'camp_id', 'position_id', 'level', 'exp', 'refine_level', \
                  'deleted', 'create_time', 'update_time', 'del_time', 'aux_data' ),
                  ('create_time', 'update_time', 'del_time')),
  
  'bag_treasureshard': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'deleted', 'create_time', 'update_time', 'del_time', 'aux_data' ),
                  ('create_time', 'update_time', 'del_time')),

           'bag_jade': (( 'id', 'cid', 'item_type', 'item_id', 'item_num', 'camp_id', 'position_id', 'level', 'exp', \
                  'deleted', 'create_time', 'update_time', 'del_time' ),
                  ('create_time', 'update_time', 'del_time')),
  
     'climbing_tower': (( 'id', 'cid', 'cur_layer', 'max_layer', 'free_reset', 'buyed_reset', 'left_buy_reset', 'free_fight', \
                  'buyed_fight', 'start_datetime', 'last_datetime' ),
                  ('last_datetime', )),

         'elitescene': (( 'id', 'cid', 'free_fight', 'buyed_fight', 'left_buy_fight', 'last_datetime' ),
                  ('last_datetime', )),

        'activescene': (( 'id', 'cid', 'panda_free', 'panda_buyed', 'panda_left_buy', 'treasure_free', 'treasure_buyed', \
                  'treasure_left_buy', 'tree_free', 'tree_buyed', 'tree_left_buy', 'last_datetime' ),
                  ('last_datetime', )),

        'atlaslist': (('id', 'cid', 'fellow_ids', 'equip_ids', 'treasure_ids'), []),

         'goodwill': (('id', 'cid', 'fellow_id', 'goodwill_exp', 'goodwill_level', 'last_gift'), []),

        }


