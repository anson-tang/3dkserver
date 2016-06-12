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


if __name__ == "__main__":
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    sql_account   = 'SELECT `account`,`id` FROM tb_character'
    sql_fellow    = 'SELECT `cid`, `fellow_id` FROM tb_fellow WHERE `cid`=%s AND `fellow_id`>100'
    
    insert_sql    = 'INSERT INTO tb_goodwill (cid, fellow_id, goodwill_exp, goodwill_level, last_gift) VALUES (%s,%s,%s,%s,%s)'
    truncate_sql  = 'TRUNCATE TABLE tb_goodwill;'
    
    cursor.execute( truncate_sql )
    cursor.execute( sql_account )
    _dataset = cursor.fetchall()
    
    _params  = []
    for _account, _cid in _dataset:
        cursor.execute( sql_fellow%_cid )
        _fellows = cursor.fetchall()
        for _cid, _fellow_id in _fellows:
            conf = get_fellow_by_fid( _fellow_id )
            if not conf:
                continue
    
            if conf['Quality'] >= 3:
                _params.append( (_cid, _fellow_id, 0, 0, 0) )
    
    if _params:
        n = cursor.executemany( insert_sql, _params )
        print 'insert_sql: ', n
 
    conn.commit()
 
    cursor.close()
    conn.close()
 
    print 'end...'
    conn   = None
    cursor = None





