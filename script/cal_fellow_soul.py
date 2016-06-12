#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Ethon Huang <huangxiaohen2738@gmail.com>
# License: Copyright(c) 2015 Ethon.Huang
# Summary: 


import MySQLdb
import sys
import os

lib_path  = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../lib')
game_path = os.path.abspath(os.path.abspath(os.path.dirname(__file__))+'/../gameserver')
sys.path.insert(0, lib_path)
sys.path.insert(0, game_path)


from twisted.internet import defer
from twisted.internet import reactor

from db_conf     import db_conf, redis_conf
from marshal     import loads, dumps
from time import time


def send_monthly_card_reward():
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()

    source ='(73003,73005,73008,73009,73011,73015,73019,73020,73021,73027,73035,73036,73037,73039,73042,73043,73045,73051,73057,73059,73060,73061,73062,73070,73071,73073,73074,73075,73076,73080,73094,73096,73100,73004,73006,73017,73018,73025,73026,73033,73038,73040,73046,73050,73072,73077,73079,73083,73084,73091)'
    print 'send begin!'
    cid_sql = 'select id, cid, item_type, item_id, item_num from tb_bag_fellowsoul where deleted = 0 and item_id in %s ;'
    update_sql = 'update tb_bag_fellowsoul set deleted = 1 where id = %s'
    insert_sql = 'insert into tb_bag_fellowsoul (cid, item_type, item_id, item_num) values(%s, %s, %s, %s)'
    
    dic = {}
    update_list = []
    cursor.execute( cid_sql % source)
    _all_cid = cursor.fetchall()
    for _id, _cid, _item_type, _item_id, _item_num in _all_cid:
        update_list.append(_id)
        if not dic.has_key(_cid):
            dic[_cid] = {_item_id : [_cid, _item_type, _item_id, _item_num]}
        else:
            if dic[_cid].has_key(_item_id):
                dic[_cid][_item_id][3] += _item_num
            else:
                dic[_cid][_item_id] = [_cid, _item_type, _item_id, _item_num]


    insert_list = []
    for _cid, _k in dic.iteritems():
        for _id, _info in _k.iteritems():
            _mod = _info[-1] % 50
            _n = _info[-1] / 50
            _sql1 = (_cid, _info[1], _info[2], _mod)
            insert_list.append(_sql1)
            _sql2 = (_cid, _info[1], _info[2], 50)
            if _n > 0:
                for i in range(_n):
                    insert_list.append(_sql2)
    
    cursor.executemany(update_sql, update_list)
    conn.commit()
    
    cursor.executemany(insert_sql, insert_list)
    conn.commit()

    cursor.close()
    conn.close()
 
    print 'end...'
    conn   = None
    cursor = None
    reactor.stop()


if __name__ == "__main__":
    reactor.callLater(1, send_monthly_card_reward)
    reactor.run()




