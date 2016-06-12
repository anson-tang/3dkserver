#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'keyword_back_up.xls'
table_name = 'tb_keyword'

field_base = '`k`', '`v`'
sql_base = 'SELECT %s FROM %s' % (','.join(field_base), table_name)
sql_base_tpl = 'SELECT %s FROM {0}' % (','.join(field_base))
#insert_sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name, ','.join(field_base), ','.join(['%s'] * (len(field_base))))
insert_sql = 'INSERT INTO {0} (%s) VALUES (%s)' % (','.join(field_base), ','.join(['%s'] * (len(field_base))))

IMPORT_SQLS = {
        'Message' : [insert_sql, table_name],  # 第二个元素为数据表名
    }

EXPORT_SQLS = {
        table_name : [sql_base_tpl, field_base, 'Message'],
    }

@route("/keyword")
@route("/keyword/<lang:int>")
def keyword_index(db, lang=0):
    db.execute('SELECT lang_id,lang_area FROM tb_lang')
    data = db.fetchall()
    return template('keyword_index', all_lang=data, lang=lang)

@route("/keyword/page")
def keyword_page(db):
    _q = request.query
    _lang = _q.lang

    last_col = '''<button id="delete" style="widht:20px;height:20px;" onclick="return keyword_delete('{0}');">删除</button>'''
    _table = 'tb_keyword_%s' % _lang if _lang and _lang != '0' else table_name

    _sql = sql_base_tpl.format( _table ) + ' %s %s %s'
    _filter_sql = 'SELECT SQL_CALC_FOUND_ROWS %s FROM {0} %s %s %s'.format(_table)
    _len_sql = 'SELECT COUNT(*) FROM {0}'.format(_table)

    limit = "LIMIT {0},{1}".format(_q.iDisplayStart, _q.iDisplayLength)
    order = 'ORDER BY '
    for i in xrange(int(_q.iSortingCols)):
        _attr = 'iSortCol_%d' % i

        if getattr(_q, 'bSortable_%s' % getattr(_q, _attr)) == 'true':
            asc = getattr(_q, 'sSortDir_%d' % i)
            order += '%s %s, ' % (field_base[int(getattr(_q, _attr))], asc)

    order = order[:-2]
    if len(order) <= 8:
        order = ''

    where = ''
    if _q.sSearch:
        where = 'WHERE ('
        for f in field_base:
            where += '{0} LIKE "%{1}%" OR '.format( f, _q.sSearch )
        where = where[:-3] + ')'

    for i in xrange(len(field_base)):
        _attr = getattr( _q, 'bSearchable_%d' % i, None )
        if _attr == 'true':
            _attr = getattr( _q, 'sSearch_%d' % i, '' )
            if _attr:
                where = ' AND ' if where else 'WHERE '
                where += '`{0}` LIKE "%{1}%"'.format( field_base[i], _attr )

    _sql = _sql % ( where, order, limit )
    _s_fields = ','.join( ( '%s' % f for f in field_base ) )
    _filter_sql = _filter_sql % ( _s_fields, where, order, limit )
    pprint('[ keyword_page ]: _filter_sql:', _filter_sql)

    db.execute( _filter_sql )
    db.execute( 'SELECT FOUND_ROWS()' )
    _filtered = db.fetchone()[0]

    db.execute( _len_sql )
    _total = db.fetchone()[0]
    _echo = _q.sEcho

    pprint('[ keyword_page ]: sql:', _sql )

    db.execute( _sql )
    _aadata = [ r + ( last_col.format( r[0] ), ) for r in db.fetchall() ]

    data = {
            'sEcho': int(_echo),
            'iTotalRecords': _total,
            'iTotalDisplayRecords': _filtered,
            'aaData': _aadata
            }

    return data

@route("/keyword/delete", method="POST")
def keyword_delete(db):
    db.execute('SELECT lang_id FROM tb_lang')
    data = db.fetchall()

    all_table = [ 'tb_keyword_%s' % lang_id for lang[0] in data ]
    all_table.append( 'tb_keyword' )

    key = request.forms.key.strip()

    for table in all_table:
        sql = 'DELETE FROM %s WHERE k="%s"' % (table_name, key)
        try:
            db.execute(sql)
        except Exception, e:
            pprint('[ keyword_delete ]:sql', sql)
            return {'result':1, 'data':str(e)}

    return {'result':0, 'data':''}

@route("/keyword/import", method="POST")
def keyword_import(db):
    data = request.files.data
    error = ''
    lang_id = int(request.forms.lang)

    _table = 'tb_keyword_%s' % lang_id if lang_id and lang_id != '0' else table_name

    all_sqls    = { 'Message' : [insert_sql.format( _table ), _table] }
    export_sqls = { _table : [sql_base_tpl.format( _table ), field_base, 'Message'] }

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpkeyword_%Y%m%d%H%M%S.xls'))
        tmp_file = open(tmp_filename, 'w')  # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件中
        rows = data.file.readlines()

        if not rows:  # 文件空
            error = '数据格式错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 在导入新的数据前，先将数据库原有数据导出到tmp目录，作为备份，数据导入失败时可以恢复数据
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
        redirect("/keyword")

@route("/keyword/export/<lang:int>")
def keyword_export(lang, db):
    tmp_root = './tmp/'
    filename = current_time("keyword_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    _table = 'tb_keyword_%s' % lang if lang and lang != '0' else table_name
    all_sqls = { _table : [sql_base_tpl.format( _table ), field_base, 'Message'] }

    if not isfile(tmp_root + filename): 
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

