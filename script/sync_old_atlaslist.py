#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb
import sys
sys.path.insert(0, '../lib')
sys.path.insert(0, '../gameserver')
from system      import *
from db_conf     import db_conf
from marshal     import dumps


def get_all_items(category_id):
    ''' 获取有图鉴的item_id列表 
    @param: category_id:1-fellow 2-equip 3-treasure
    '''
    _category_conf = get_atlaslist_category_conf(category_id)
    for _second_conf in _category_conf.itervalues():
        for _star_conf in _second_conf.itervalues():
            for _item in _star_conf['Items']:
                if _item['ItemID'] not in _all_items:
                    _all_items.append(_item['ItemID'])


ALL_FELLOW_IDS = [21029,21030,21031,21032,21033,21034,21035,21036,22033,22034,22035,22036,22037,22038,22039,22040,22041,22042,23018,23042,23043,23045,23046,23013,23014,23015,23019,23020,23021,23022,23044,23047,23048,23055,23056,21037,21038,21039,21040,21041,21042,21043,21044,22043,22044,22045,22046,22047,22048,22049,22050,22051,22052,23033,23037,23038,23039,23040,23050,23030,23031,23032,23034,23036,23041,23049,23051,23052,23053,23054,23098,21045,21046,21047,21048,21049,21050,21051,21052,22053,22054,22055,22056,22057,22058,22059,22060,22061,22062,23025,23026,23059,23060,23061,23062,23024,23057,23058,23063,23064,23065,23066,23067,23068,23069,23097,21004,21005,21006,21009,21010,21011,22003,22004,22009,22010,22015,22016,22017,22018,22019,22020,23004,23005,23006,23008,23017,23070,23003,23012,23027,21001,21002,21003,21012,21013,21014,21015,21016,21017,21018,21019,21020,21021,21022,21023,21024,21025,21026,21028,22001,22002,22007,22008,22011,22012,22013,22014,22021,22022,22023,22024,22025,22026,22027,22028,22029,22030,23009,23011,23077,23079,23100,23001,23002,23007,23010,23016,23023,23076,23078,23080,23099,21007,21008,21027,22005,22006,22031,22032,22063,22064,22065,22066,22067,22068,22069,22070,22071,23072,23083,23084,23091,23094,23096,23028,23029,23035,23071,23073,23074,23075,23081,23082,23085,23086,23087,23088,23089,23090,23092,23093,23095]

ALL_EQUIP_IDS = [11001,11002,11003,11004,11005,11006,11007,11008,11009,12001,12002,12003,12004,12005,12006,12007,12008,12009,13001,13002,13003,13004,13005,13006,13007,13008,13009,14001,14002,14003,14004,14005,14006,14007,14008,14009,14999]

ALL_TREASURE_IDS = [31001,31002,31003,31004,31005,31006,32001,32002,32003,32004,32005,32006,32999,33001,33002,33003,33004,33005,33006,33999,51001,51002,51003,51004,51005,51006,52001,52002,52003,52004,52005,52006,52999,53001,53002,53003,53004,53005,53006,53999]

if __name__ == "__main__":
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
 
    sql_account   = 'SELECT `id` FROM tb_character;'
    sql_fellow    = 'SELECT DISTINCT(fellow_id) FROM tb_fellow WHERE `cid`=%s AND `fellow_id`>100;'
    sql_equip     = 'SELECT DISTINCT(item_id) FROM tb_bag_equip WHERE `cid`=%s;'
    sql_treasure  = 'SELECT DISTINCT(item_id) FROM tb_bag_treasure WHERE `cid`=%s;'
 
    insert_sql    = 'INSERT INTO tb_atlaslist (cid, fellow_ids, equip_ids, treasure_ids) VALUES (%s,%s,%s,%s);'
    truncate_sql  = 'TRUNCATE TABLE tb_atlaslist;'
 
    cursor.execute( truncate_sql )
    cursor.execute( sql_account )
    _dataset = cursor.fetchall()
 
    for _cid, in _dataset:
        _params  = []
        # 伙伴
        cursor.execute( sql_fellow%_cid )
        _fellow_ids = []
        _fellows = cursor.fetchall()
        for _item_id, in _fellows:
            if _item_id in ALL_FELLOW_IDS:
                _fellow_ids.append( _item_id )
 
        # 装备
        cursor.execute( sql_equip%_cid )
        _equip_ids = []
        _equips = cursor.fetchall()
        for _item_id, in _equips:
            if _item_id in ALL_EQUIP_IDS:
                _equip_ids.append( _item_id )
 
        # 装备
        cursor.execute( sql_treasure%_cid )
        _treasure_ids = []
        _treasures = cursor.fetchall()
        for _item_id, in _treasures:
            if _item_id in ALL_TREASURE_IDS:
                _treasure_ids.append( _item_id )
 
        if _fellow_ids or _equip_ids or _treasure_ids:
            _params = [_cid, dumps(_fellow_ids), dumps(_equip_ids), dumps(_treasure_ids)]

        if _params:
            n=cursor.execute( insert_sql, _params )
 
    conn.commit()
 
    cursor.close()
    conn.close()
 
    print 'insert_sql: ', n
    print 'end...'
    conn   = None
    cursor = None





