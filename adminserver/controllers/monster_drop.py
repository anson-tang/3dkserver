#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

MONSTER_DROP_BACK_FILE = 'monster_drop_back_up.xls'
TABLE_NAME = 'tb_monster_drop'

field_monster_drop = 'DropID', 'MonsterID', 'MonsterDiff', 'ItemType', 'ItemID', 'RateStart', 'RateAdd', 'RateMax', 'ItemNum', 'ActiveID'
sql_monster_drop   = 'SELECT %s FROM tb_monster_drop' % ','.join(field_monster_drop)
insert_sql_skill   = 'INSERT INTO tb_monster_drop (%s) VALUES (%s)' % (','.join(field_monster_drop), ','.join(['%s'] * len(field_monster_drop)))

MONSTER_DROP_IMPORT_SQLS = {
        'monster_drop'   : [insert_sql_skill, 'tb_monster_drop'],
    }

MONSTER_DROP_EXPORT_SQLS = {
        'tb_monster_drop' : [sql_monster_drop, field_monster_drop, 'monster_drop'],
    }

@route("/monster_drop")
@route("/monster_drop/<lang:int>")
def monster_drop_index(db, lang=0):
    db.execute(sql_monster_drop)
    data = db.fetchall()
    return template('monster_drop', data=data, lang=lang)

@route("/monster_drop/page")
def item_page(db):
    _q = request.query
    _lang = _q.lang

    last_col = '''<button id="delete" style="widht:20px;height:20px;" onclick="return monster_drop_delete('{0}');">删除</button>'''
    _table = 'tb_monster_drop_%s' % _lang if _lang and _lang != '0' else TABLE_NAME

    _sql = sql_monster_drop.format( _table ) + ' %s %s %s'
    _filter_sql = 'SELECT SQL_CALC_FOUND_ROWS %s FROM {0} %s %s %s'.format(_table)
    _len_sql = 'SELECT COUNT(*) FROM {0}'.format(_table)

    limit = "LIMIT {0},{1}".format(_q.iDisplayStart, _q.iDisplayLength)
    order = 'ORDER BY '
    for i in xrange(int(_q.iSortingCols)):
        _attr = 'iSortCol_%d' % i

        if getattr(_q, 'bSortable_%s' % getattr(_q, _attr)) == 'true':
            asc = getattr(_q, 'sSortDir_%d' % i)
            order += '%s %s, ' % (field_monster_drop[int(getattr(_q, _attr))], asc)

    order = order[:-2]
    if len(order) <= 8:
        order = ''

    where = ''
    if _q.sSearch:
        where = 'WHERE ('
        for f in field_monster_drop:
            where += '{0} LIKE "%{1}%" OR '.format( f, _q.sSearch )
        where = where[:-3] + ')'

    for i in xrange(len(field_monster_drop)):
        _attr = getattr( _q, 'bSearchable_%d' % i, None )
        if _attr == 'true':
            _attr = getattr( _q, 'sSearch_%d' % i, '' )
            if _attr:
                where = ' AND ' if where else 'WHERE '
                where += '`{0}` LIKE "%{1}%"'.format( field_monster_drop[i], _attr )

    _sql = _sql % ( where, order, limit )
    _s_fields = ','.join( ( '%s' % f for f in field_monster_drop ) )
    _filter_sql = _filter_sql % ( _s_fields, where, order, limit )
    pprint('[ monster_drop_page ]: _filter_sql:', _filter_sql)

    db.execute( _filter_sql )
    db.execute( 'SELECT FOUND_ROWS()' )
    _filtered = db.fetchone()[0]

    db.execute( _len_sql )
    _total = db.fetchone()[0]
    _echo = _q.sEcho

    pprint('[ monster_drop_page ]: sql:', _sql )

    db.execute( _sql )
    _aadata = [ r + ( last_col.format( r[0] ), ) for r in db.fetchall() ]

    data = {
            'sEcho': int(_echo),
            'iTotalRecords': _total,
            'iTotalDisplayRecords': _filtered,
            'aaData': _aadata
            }

    return data

@route("/monster_drop/delete", method="POST")
def monster_drop_delete(db):
    sid = request.forms.sid.strip()
    sql = 'DELETE FROM tb_monster_drop WHERE ball_id=%s;' % sid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/monster_drop/import", method="POST")
def monster_drop_import(db):
    data = request.files.data
    error = ''
    all_sqls = MONSTER_DROP_IMPORT_SQLS 

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpskillball_%Y%m%d%H%M%S.xls'))
        tmp_file = open(tmp_filename, 'w')  # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件中
        rows = data.file.readlines()

        if not rows:  # 文件空
            error = '数据格式错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 在导入新的数据前，先将数据库原有数据导出到tmp目录，作为备份，数据导入失败时可以恢复数据
        export_sqls = MONSTER_DROP_EXPORT_SQLS
        try:
            # 若备份文件已存在，则删除重新写入
            if os.path.exists(os.path.join(tmp_root, MONSTER_DROP_BACK_FILE)):
                os.remove(os.path.join(tmp_root, MONSTER_DROP_BACK_FILE))
            excel_export(export_sqls, tmp_root, MONSTER_DROP_BACK_FILE, db)
        except Exception, e:
            print '数据备份错误: %s' %e

        error = excel_import(all_sqls, tmp_filename, db)
        os.remove(tmp_filename)  # 删除上传的临时文件
    else:  # 没有文件
        error = '数据格式错误[1]'

    if error:
        # 导入数据错误，进行数据恢复
        try:
            excel_import(all_sqls, os.path.join(tmp_root, MONSTER_DROP_BACK_FILE), db)
            print '数据恢复成功'
        except Exception, e:
            print '数据恢复错误: %s' %e
        return template('error', error=error + '    数据已恢复')
    else:
        redirect("/monster_drop")

@route("/monster_drop/export")
def monster_drop_export(db):
    tmp_root = './tmp/'
    filename = current_time("monster_drop_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = MONSTER_DROP_EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/monster_drop/recover")
def monster_drop_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, MONSTER_DROP_BACK_FILE)
    error = ''
    if not isfile(filename):
        error = '没有备份文件'
        return template('error', error=error)
    all_sqls = MONSTER_DROP_IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error= '数据恢复失败，原因：' + error)
    else:
        redirect('/monster_drop')

