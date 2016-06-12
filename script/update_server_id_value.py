#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb

from db_conf     import db_conf

USERDB_CONF = {
        '3dk_heitao_s1_userdb':1001,
        '3dk_heitao_s2_userdb':1002,
        '3dk_heitao_s3_userdb':1003,
        '3dk_heitao_s4_userdb':1004,
        }


if __name__=="__main__":
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    sql_update = 'UPDATE tb_character SET sid=%s WHERE id>0;'

    # update sid
    server_id = USERDB_CONF.get(db_conf['db'], 0)
    if server_id:
        print "update sql:", sql_update%server_id
        cursor.execute( sql_update%server_id )
        conn.commit()

    print 'end...'
    cursor.close()
    conn.close()
    
    conn   = None
    cursor = None





