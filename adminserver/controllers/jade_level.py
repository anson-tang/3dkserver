#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

SCENE_BACK_FILE = 'jade_level_back_up.xls'

field_jade_level = 'ID', 'JadeLevel', 'TargetLevel', 'Rate', 'ExtraOdds', 'ItemType', 'ItemID', 'ItemNum'
sql_jade_level   = 'SELECT %s FROM tb_jade_level' % ','.join(field_jade_level)
insert_sql       = 'INSERT INTO tb_jade_level VALUES (%s)' % ','.join(['%s'] * len(field_jade_level))

field_jade_cost      = 'JadeLevel', 'CostItemType', 'CostItemID', 'CostItemNum'
sql_jade_cost        = 'SELECT %s FROM tb_jade_cost' % ','.join(field_jade_cost)
insert_sql_jade_cost = 'INSERT INTO tb_jade_cost VALUES (%s)' % ','.join(['%s'] * len(field_jade_cost))
get_jade_cost        = 'SELECT %s FROM tb_jade_cost WHERE JadeLevel=%s'

excel_name      = 'JadeLevel'
sub_excel_name  = 'JadeCost'
excel_export_filename = "JadeLevel_%Y%m%d%H%M.xls"

IMPORT_SQLS = {
        excel_name  : [insert_sql, 'tb_jade_level'],  # 若目录tmp_root不存在，则创建
    sub_excel_name  :[insert_sql_jade_cost, 'tb_jade_cost'],
    }

EXPORT_SQLS = {
        'tb_jade_level'            : [sql_jade_level, field_jade_level, excel_name],
        'tb_jade_cost'    : [sql_jade_cost, field_jade_cost, sub_excel_name],
    }


@route("/jade_level")
def jade_level_index(db):
    db.execute(sql_jade_level)
    data = db.fetchall()
    return template('jade_level_index', data=data)

@route("/jade_level/delete", method="POST")
def jade_level_delete(db):
    sid = request.forms.sid.strip()
    sql = 'DELETE FROM tb_jade_level WHERE GroupID=%s;' % sid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/jade_level/import", method="POST")
def jade_level_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpjade_level_%Y%m%d%H%M%S.xls'))
        tmp_file = open(tmp_filename, 'w') # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件中
        rows = data.file.readlines()

        if not rows: # 文件空 
            error = '数据格式错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 在导入新的数据前，先将数据库原有数据导出到tmp目录，作为备份，数据导入失败时可以恢复数据
        export_sqls = EXPORT_SQLS
        try:
            # 若备份文件已存在，则删除重新写入
            if os.path.exists(os.path.join(tmp_root, SCENE_BACK_FILE)):
                os.remove(os.path.join(tmp_root, SCENE_BACK_FILE))
            excel_export(export_sqls, tmp_root, SCENE_BACK_FILE, db)
        except Exception, e:
            print '数据备份错误: %s' %e

        error = excel_import(all_sqls, tmp_filename, db)
        os.remove(tmp_filename) # 删除上传的临时文件
    else:  # 没有文件
        error = '数据格式错误[1]'

    if error:
        # 导入数据错误，进行数据恢复
        try:
            excel_import(all_sqls, os.path.join(tmp_root, SCENE_BACK_FILE), db)
            print '数据恢复成功'
        except Exception, e:
            print '数据恢复错误: %s' %e
        return template('error', error=error + '    数据已恢复')
    else:
        redirect("/jade_level")

@route("/jade_level/export")
def jade_level_export(db):
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

@route("/jade_level/recover")
def jade_level_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, SCENE_BACK_FILE)
    error = ''
    if not isfile(filename):
        error = '没有备份文件'
        return template('error', error=error)
    all_sqls = IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error= '数据恢复失败，原因：' + error)
    else:
        redirect('/jade_level')

@route("/jade_level/list/get", method="POST")
def jade_cost_get(db):
    sid = request.forms.sid.strip()
    #db.execute('SELECT Turn,MonsterList,MonsterAttrList FROM tb_jade_cost WHERE GroupID=%s', (sid, ))
    db.execute( get_jade_cost % (','.join(field_jade_cost[1:]), sid) )
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}
 
@route("/jade_level/dellist", method="POST")
def jade_cost_del(db):
    sid = request.forms.sid.strip()
    db.execute('DELETE FROM tb_jade_cost WHERE JadeLevel=%s', (sid,))
    return {'result': 0, 'data':''}
  
    
