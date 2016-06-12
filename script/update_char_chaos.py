#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Anson Tang <anson.tkg@gmail.com>
# License: Copyright(c) 2015 Anson.Tang
# Summary: 

import MySQLdb

from db_conf import db_conf



def main():
    db     = MySQLdb.connect(**db_conf)
    cursor = db.cursor()

    sql_select = 'SELECT id,lead_id,chaos_level FROM tb_character;'
    sql_update = 'UPDATE tb_character SET lead_id=%s WHERE id=%s;'
    cursor.execute( sql_select )


    chaos_level = [156, 56, 16, 1, 0]
    lead_man    = [9, 7, 5, 3, 1]
    lead_women  = [10, 8, 6, 4, 2]
    dataset = cursor.fetchall()
    for row in dataset:
        for _idx, _level in enumerate(chaos_level):
            if row[2] >= _level:
                if row[1] in lead_man:
                    if row[1] != lead_man[_idx]:
                        cursor.execute( sql_update%(lead_man[_idx], row[0]) )
                        #print row, (row[0], lead_man[_idx])
                elif row[1] != lead_women[_idx]:
                    cursor.execute( sql_update%(lead_women[_idx], row[0]) )
                    #print row, (row[0], lead_women[_idx])
                break

    db.commit()
    cursor.close()
    db.close()
    print 'end...'
    db     = None
    cursor = None


if __name__=="__main__": main()


