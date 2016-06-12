#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb
import traceback

from constant      import *
from log           import log
from utils         import split_items



def guild_sacrifice_data_handler(table, fields, dataset):
    _data = {}
    for row in dataset:
        if _data.has_key(row[0]):
            continue
        _data[row[0]] = split_items( row[1] )

    return _data

def guild_shop_limit_data_handler(table, fields, dataset):
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


TABLES = (
        (FOR_SERVER_ONLY, 'vip', ('VipLevel', 'GuildSacrificeCount'), None, None),
        (FOR_SERVER_ONLY, 'guild_level', ('Level', 'GuildHall', 'GuildDungeon', 'GuildWelfareHall', 'GuildShop', 'GuildTask', 'MembersCount'), None, None),
        (FOR_SERVER_ONLY, 'guild_sacrifice', ('Level', 'AwardList'), None, guild_sacrifice_data_handler),
        (FOR_SERVER_ONLY, 'guild_shop_limit', ('ID', 'GuildLevel', 'ItemType', 'ItemID', 'ItemNum', 'Cost', 'BuyMax', 'Rate', 'AddRate', 'MaxRate'), None, guild_shop_limit_data_handler),
        (FOR_SERVER_ONLY, 'guild_shop_item', ('ID', 'GuildLevel', 'ItemType', 'ItemID', 'ItemNum', 'Cost', 'BuyMax'), None, None),
        (FOR_SERVER_ONLY, 'guild_contribution', ('ID', 'CostItemType', 'CostItemID', 'CostItemNum', 'GuildAward', 'PersonAward', 'VipLevel'), None, guild_contribution_data_handler),

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

def load_alliance_config(limit=FOR_SERVER_ONLY):
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

    return result



