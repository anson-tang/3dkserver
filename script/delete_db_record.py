#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb

from db_conf import db_conf


if __name__ == "__main__":
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    #cursor.execute( 'SELECT count(*) FROM tb_bag_equip WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_bag_equip WHERE deleted=1;' )

    #cursor.execute( 'SELECT count(*) FROM tb_bag_equipshard WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_bag_equipshard WHERE deleted=1;' )

    #cursor.execute( 'SELECT count(*) FROM tb_bag_fellowsoul WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_bag_fellowsoul WHERE deleted=1;' )

    #cursor.execute( 'SELECT count(*) FROM tb_bag_item WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_bag_item WHERE deleted=1;' )

    #cursor.execute( 'SELECT count(*) FROM tb_bag_treasure WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_bag_treasure WHERE deleted=1;' )

    #cursor.execute( 'SELECT count(*) FROM tb_bag_treasureshard WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_bag_treasureshard WHERE deleted=1;' )

    #cursor.execute( 'SELECT count(*) FROM tb_fellow WHERE deleted=1;' )
    cursor.execute( 'DELETE FROM tb_fellow WHERE deleted=1;' )


    #cursor.fetchall()
    conn.commit()
    print('end...')
    conn   = None
    cursor = None


