#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import MySQLdb

from db_conf import db_conf





# format: {vip_level:need_payed, ...)
old_vip_conf = {0:0, 1:5, 2:55, 3:155, 4:355, 5:655, 6:1155, 7:2155, 8:4155, 9:7155, 10:12155, 11:22155, 12:42155, 13:92155, 14:192155, 15:492155}
#print('For Test. old_vip_conf: {0}.'.format( old_vip_conf ))
new_vip_conf = {0:0, 1:5, 2:50, 3:100, 4:200, 5:300, 6:500, 7:1000, 8:2000, 9:3000, 10:5000, 11:10000, 12:20000, 13:50000, 14:100000, 15:300000}
#print('For Test. new_vip_conf: {0}.'.format( new_vip_conf ))

def cal_new_vip_level(cid, vip_level, payed):
    '''
    @param: vip_level-玩家之前的vip等级
    @param: payed-玩家之前等级下剩余的点卷
    '''
    _final_level = 0
    _old_total_payed = old_vip_conf.get(vip_level) + payed
    #print('For Test. old info. cid: {0}, vip_level: {1}, payed: {2}, total_payed: {3}.'.format( cid, vip_level, payed, _old_total_payed ))
    while _old_total_payed > 0:
        _need_pay = new_vip_conf.get( _final_level+1, 0 )
        if not _need_pay or _old_total_payed < _need_pay:
            break
        _final_level += 1

    _old_total_payed -= new_vip_conf[_final_level]

    #print('For Test. new info. cid: {0}, vip_level: {1}, payed: {2}.'.format( cid, _final_level, _old_total_payed ))
    return _final_level, _old_total_payed, old_vip_conf.get(vip_level) + payed


if __name__ == "__main__":
    conn = MySQLdb.connect(**db_conf)
    cursor = conn.cursor()
    
    sql_vip_info = 'SELECT `id`,`vip_level`,`credits_payed` FROM tb_character WHERE vip_level>0 or credits_payed>0;'
    
    sql_update   = 'UPDATE tb_character SET vip_level=%s,credits_payed=%s,total_cost=%s WHERE id=%s;'
    
    cursor.execute( sql_vip_info )
    _dataset = cursor.fetchall()
    
    _params = []
    for _cid, _vip_level, _payed in _dataset:
        _new_vip_level, _new_payed, _total_pay = cal_new_vip_level(_cid, _vip_level, _payed)
        _params.append( [_new_vip_level, _new_payed, _total_pay, _cid] )
 
    if _params:
        cursor.executemany( sql_update, _params )
        print('update user<{0}> vip_level success.'.format( len(_params) ))
 
    cursor.fetchall()
    conn.commit()
 
    print('end...')
    conn   = None
    cursor = None



