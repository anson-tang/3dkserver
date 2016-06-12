#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'arena_rank_award_back_up.xls'
TABLE_NAME = 'tb_arena_rank_award'
field_arena_rank_award = 'ArenaRank', 'ArenaRankList'
del_sql_arena_rank_award = 'DELETE FROM tb_arena_rank_award WHERE ArenaRank=%s;'

sql_arena_rank_award   = 'SELECT %s FROM tb_arena_rank_award' % ','.join(field_arena_rank_award)
insert_sql_arena_rank_award = 'INSERT INTO tb_arena_rank_award (%s) VALUES (%s)' % (','.join(field_arena_rank_award), ','.join(['%s'] * len(field_arena_rank_award)))

excel_name = 'ArenaRankAward'
excel_export_filename = "ArenaRankAward_%Y%m%d%H%M.xls"

IMPORT_SQLS = {
        excel_name   : [insert_sql_arena_rank_award, 'tb_arena_rank_award'],
    }

EXPORT_SQLS = {
        'tb_arena_rank_award' : [sql_arena_rank_award, field_arena_rank_award, excel_name],
    }

@route("/arena_rank_award")
@route("/arena_rank_award/<lang:int>")
def arena_rank_award_index(db, lang=0):
    db.execute(sql_arena_rank_award)
    data = db.fetchall()
    return template('arena_rank_award_index', data=data, lang=lang)

@route("/arena_rank_award/page")
def arena_rank_award_page(db):
    _q = request.query
    _lang = _q.lang

    last_col = '''<button id="delete" style="widht:20px;height:20px;" onclick="return arena_rank_award_delete('{0}');">删除</button>'''
    _table = 'tb_arena_rank_award_%s' % _lang if _lang and _lang != '0' else TABLE_NAME

    _sql = sql_arena_rank_award.format( _table ) + ' %s %s %s'
    _filter_sql = 'SELECT SQL_CALC_FOUND_ROWS %s FROM {0} %s %s %s'.format(_table)
    _len_sql = 'SELECT COUNT(*) FROM {0}'.format(_table)

    limit = "LIMIT {0},{1}".format(_q.iDisplayStart, _q.iDisplayLength)
    order = 'ORDER BY '
    for i in xrange(int(_q.iSortingCols)):
        _attr = 'iSortCol_%d' % i

        if getattr(_q, 'bSortable_%s' % getattr(_q, _attr)) == 'true':
            asc = getattr(_q, 'sSortDir_%d' % i)
            order += '%s %s, ' % (field_arena_rank_award[int(getattr(_q, _attr))], asc)

    order = order[:-2]
    if len(order) <= 8:
        order = ''

    where = ''
    if _q.sSearch:
        where = 'WHERE ('
        for f in field_arena_rank_award:
            where += '{0} LIKE "%{1}%" OR '.format( f, _q.sSearch )
        where = where[:-3] + ')'

    for i in xrange(len(field_arena_rank_award)):
        _attr = getattr( _q, 'bSearchable_%d' % i, None )
        if _attr == 'true':
            _attr = getattr( _q, 'sSearch_%d' % i, '' )
            if _attr:
                where = ' AND ' if where else 'WHERE '
                where += '`{0}` LIKE "%{1}%"'.format( field_arena_rank_award[i], _attr )

    _sql = _sql % ( where, order, limit )
    _s_fields = ','.join( ( '%s' % f for f in field_arena_rank_award ) )
    _filter_sql = _filter_sql % ( _s_fields, where, order, limit )
    pprint('[ arena_rank_award_page ]: _filter_sql:', _filter_sql)

    db.execute( _filter_sql )
    db.execute( 'SELECT FOUND_ROWS()' )
    _filtered = db.fetchone()[0]

    db.execute( _len_sql )
    _total = db.fetchone()[0]
    _echo = _q.sEcho

    pprint('[ arena_rank_award_page ]: sql:', _sql )

    db.execute( _sql )
    _aadata = [ r + ( last_col.format( r[0] ), ) for r in db.fetchall() ]

    data = {
            'sEcho': int(_echo),
            'iTotalRecords': _total,
            'iTotalDisplayRecords': _filtered,
            'aaData': _aadata
            }
    return data
@route("/arena_rank_award/delete", method="POST")
def arena_rank_award_delete(db):
    sid = request.forms.sid.strip()
    #sql = 'DELETE FROM tb_arena_rank_award WHERE Rank=%s;' % sid
    sql = del_sql_arena_rank_award % sid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/arena_rank_award/import", method="POST")
def arena_rank_award_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS 

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmp_arena_rank_award%Y%m%d%H%M%S.xls'))
        tmp_file = open(tmp_filename, 'w')  # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件中
        rows = data.file.readlines()

        if not rows:  # 文件空
            error = '数据格式错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 在导入新的数据前，先将数据库原有数据导出到tmp目录，作为备份，数据导入失败时可以恢复数据
        export_sqls = EXPORT_SQLS
        try:
            # 若备份文件已存在，则删除重新写入
            if os.path.exists(os.path.join(tmp_root, BACK_FILE)):
                os.remove(os.path.join(tmp_root, BACK_FILE))
            excel_export(export_sqls, tmp_root, BACK_FILE, db)
        except Exception, e:
            print '数据备份错误: %s' %e

        error = excel_import(all_sqls, tmp_filename, db)
        os.remove(tmp_filename)  # 删除上传的临时文件
    else:  # 没有文件
        error = '数据格式错误[1]'

    if error:
        # 导入数据错误，进行数据恢复
        try:
            excel_import(all_sqls, os.path.join(tmp_root, BACK_FILE), db)
            print '数据恢复成功'
        except Exception, e:
            print '数据恢复错误: %s' %e
        return template('error', error=error + '    数据已恢复')
    else:
        redirect("/arena_rank_award")

@route("/arena_rank_award/export")
def arena_rank_award_export(db):
    tmp_root = './tmp/'
    filename = current_time(excel_export_filename)  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/arena_rank_award/recover")
def arena_rank_award_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, BACK_FILE)
    error = ''
    if not isfile(filename):
        error = '没有备份文件'
        return template('error', error=error)
    all_sqls = IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error= '数据恢复失败，原因：' + error)
    else:
        redirect('/arena_rank_award')

