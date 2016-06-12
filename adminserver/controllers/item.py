#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'item_back_up.xls'
TABLE_NAME = 'tb_item'

field_base = 'ItemID', 'ItemName', 'Description', 'UseLevel', 'Quality', 'StarLevel', 'QualityLevel', 'ItemType', 'ChangeList', 'IsUsed', 'Path', 'Icon', 'MaxOverlyingCount', 'Location', 'Price'
sql_base = 'SELECT %s FROM %s' % (','.join(field_base), TABLE_NAME)
insert_sql = 'INSERT INTO %s VALUES (%s)' % (TABLE_NAME, ','.join(['%s'] * len(field_base)))

field_attribute          = 'ItemID', 'AttributeID', 'Value', 'AddValue'
sql_attribute            = 'SELECT %s FROM tb_item_attribute' % ','.join(field_attribute)
insert_sql_attribute     = 'INSERT INTO tb_item_attribute VALUES (%s)' % ','.join(['%s'] * len(field_attribute))

field_changeitem  = 'Item', 'SubItem', 'ItemNum'
sql_changeitem    = 'SELECT %s FROM tb_item_changeitem' % ','.join(field_changeitem)
insert_sql_changeitem = 'INSERT INTO tb_item_changeitem VALUES (%s)' % ','.join(['%s'] * len(field_changeitem))

field_treasure_unlock  = 'TreasureID', 'TreasureLevel', 'AttributeID', 'AttributeValue'
sql_treasure_unlock    = 'SELECT %s FROM tb_treasure_unlock' % ','.join(field_treasure_unlock)
insert_sql_treasure_unlock = 'INSERT INTO tb_treasure_unlock VALUES (%s)' % ','.join(['%s'] * len(field_treasure_unlock))


IMPORT_SQLS = {
        'Item'              : [insert_sql, 'tb_item'],  # 第二个元素为数据表名
        'ItemAttribute'     : [insert_sql_attribute, 'tb_item_attribute'],
        'TreasureUnlock'    : [insert_sql_treasure_unlock, 'tb_treasure_unlock'],
    }

EXPORT_SQLS = {
        'tb_item'                   : [sql_base, field_base, 'Item'],
        'tb_item_attribute'         : [sql_attribute, field_attribute, 'ItemAttribute'],
        'tb_treasure_unlock'        : [sql_treasure_unlock, field_treasure_unlock, 'TreasureUnlock'],
    }


@route("/item")
@route("/item/<lang:int>")
def item_index(db, lang=0):
    db.execute(sql_base)
    data = db.fetchall()
    return template('item_index', data=data, lang=lang)

@route("/item/page")
def item_page(db):
    _q = request.query
    _lang = _q.lang

    last_col = '''<button id="delete" style="widht:20px;height:20px;" onclick="return item_delete('{0}');">删除</button>'''
    _table = 'tb_item_%s' % _lang if _lang and _lang != '0' else TABLE_NAME

    _sql = sql_base.format( _table ) + ' %s %s %s'
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
    pprint('[ item_page ]: _filter_sql:', _filter_sql)

    db.execute( _filter_sql )
    db.execute( 'SELECT FOUND_ROWS()' )
    _filtered = db.fetchone()[0]

    db.execute( _len_sql )
    _total = db.fetchone()[0]
    _echo = _q.sEcho

    pprint('[ item_page ]: sql:', _sql )

    db.execute( _sql )
    _aadata = [ r + ( last_col.format( r[0] ), ) for r in db.fetchall() ]

    data = {
            'sEcho': int(_echo),
            'iTotalRecords': _total,
            'iTotalDisplayRecords': _filtered,
            'aaData': _aadata
            }

    return data

@route("/item/delete", method="POST")
def item_delete(db):
    iid = request.forms.iid.strip()
    sql = 'DELETE FROM tb_item WHERE ItemID=%s;' % iid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/item/import", method="POST")
def item_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpitem_%Y%m%d%H%M%S.xls'))
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
        redirect("/item")

@route("/item/export")
def item_export(db):
    tmp_root = './tmp/'
    filename = current_time("item_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/item/recover")
def item_recover(db):
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
        redirect('/item')

@route("/item/attribute/get", method="POST")
def item_attribute_get(db):
    iid = request.forms.iid.strip()
    db.execute('{0} WHERE ItemID=%s'.format(sql_attribute), (iid, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}

@route("/item/changeitem/get", method="POST")
def item_changeitem_get(db):
    iid = request.forms.iid.strip()
    db.execute('{0} WHERE Item=%s'.format(sql_changeitem), (iid, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}

@route("/item/delattribute", method="POST")
def item_attribute_delete(db):
    iid = request.forms.iid.strip()
    aid = request.forms.aid.strip()
    db.execute('DELETE FROM tb_item_attribute WHERE ItemID=%s AND AttributeID=%s', ( iid, aid ))
    return {'result': 0, 'data':''}

@route("/item/delchangeitem", method="POST")
def item_changeitem_delete(db):
    iid = request.forms.iid.strip()
    siid = request.forms.siid.strip()
    db.execute('DELETE FROM tb_item_changeitem WHERE Item=%s AND SubItem=%s', ( iid, siid ))
    return {'result': 0, 'data':''}
 
@route("/item/treasureunlock/get", method="POST")
def item_treasureunlock_get(db):
    iid = request.forms.iid.strip()
    db.execute('{0} WHERE TreasureID=%s'.format(sql_treasure_unlock), (iid, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}

@route("/item/deltreasureunlock", method="POST")
def item_treasureunlock_delete(db):
    iid = request.forms.iid.strip()
    siid = request.forms.siid.strip()
    db.execute('DELETE FROM tb_treasure_unlock WHERE TreasureID=%s AND TreasureLevel=%s', ( iid, siid ))
    return {'result': 0, 'data':''}
 
