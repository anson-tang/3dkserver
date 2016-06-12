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
    
    sql_update = 'UPDATE tb_character SET energy=energy*5,douzhan=douzhan*2 WHERE id>0;'
    
    cursor.execute( sql_update )
    cursor.fetchall()
    conn.commit()

    print 'end...'
    cursor.close()
    conn.close()
    
    conn   = None
    cursor = None





