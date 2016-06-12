#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

import os
import time
import MySQLdb
import sys

from db_conf     import db_conf

def main():
    conn   = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()

    #os.system("mysqldump -u{0} -p{1} {2} > ./bak_{2}.sql".format( db_conf['user'], db_conf['passwd'], db_conf['db'] ))

    sql_select = 'SELECT %s FROM tb_character;'
    sql_update = 'UPDATE tb_character SET id=id+%d WHERE id=%d;'
    base_cnt   = 1000000

    character_fields = ( 'id', 'sid', 'account', 'nick_name', 'lead_id', 'level', 'exp', 'vip_level', 'might', 'recharge', \
                  'golds', 'credits', 'credits_payed', 'total_cost', 'firstpay', 'monthly_card', 'dual_monthly_card', 'growth_plan', 'register_time', \
                  'last_login_time', 'fellow_capacity', 'item_capacity', 'treasure_capacity', 'equip_capacity', \
                  'equipshard_capacity', 'jade_capacity', 'soul', 'hunyu', 'prestige', 'honor', 'energy', \
                  'chaos_level', 'scene_star', 'douzhan', 'tutorial_steps', 'friends', 'charge_ids' )

    cursor.execute( sql_select%(','.join(character_fields)) )
    _values = cursor.fetchall()
    if not _values:
        print 'no character data...'
        return
    error_cids = {}
    sql_insert = "INSERT INTO tb_character (" + ",".join(character_fields) + ") VALUES (" + ','.join(['%s'] * len(character_fields)) + ');'

    cursor.execute( 'TRUNCATE TABLE tb_character;' )
    len_data = len(_values)
    _idx     = 0.0
    _max_id  = 0
    for _row in _values:
        _idx += 1
        _row  = list(_row)
        if _row[0] > (_row[1]*base_cnt + 999999):
            error_cids[_row[0]] = _row[0]%base_cnt + _row[1]*base_cnt
        _row[0] = _row[0]%base_cnt

        if _row[0] > _max_id:
            _max_id = _row[0]
        cursor.execute( sql_insert, _row )
        cursor.execute( sql_update%(_row[1]*base_cnt, _row[0]) )
        if _idx % 500 == 0 or _idx >= len_data:
            sys.stdout.write("\r Progress: %s %%. len:%s." % (round((_idx / len_data) * 100, 2), len_data))
            sys.stdout.flush()
    print "\ntotal error_cids:{0}, all error_cids:{1}.".format( len(error_cids), error_cids )
    print 'update table<tb_character> max_id<%s> data success.'%(_max_id)

    conn.commit()
    cursor.close()
    conn.close()
    print 'end...'
    conn   = None
    cursor = None


if __name__=="__main__": main()


