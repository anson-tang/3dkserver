#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb

from db_conf     import db_conf


if __name__=="__main__":
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
 
    print 'start update...'
    sql_update_1 = 'UPDATE tb_activescene SET panda_left_buy=0,treasure_left_buy=0,tree_left_buy=0 WHERE id>0;'
    cursor.execute( sql_update_1 )

    sql_update_2 = 'UPDATE tb_elitescene SET left_buy_fight=0 WHERE id>0;'
    cursor.execute( sql_update_2 )

    sql_update_3 = 'UPDATE tb_climbing_tower SET free_reset=0,left_buy_reset=0,free_fight=0 WHERE id>0;'
    cursor.execute( sql_update_3 )

    conn.commit()

    print 'end...'
    cursor.close()
    conn.close()
    
    conn   = None
    cursor = None





