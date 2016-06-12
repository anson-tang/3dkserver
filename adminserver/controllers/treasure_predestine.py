#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'treasure_predestine_back_up.xls'

field_treasure_predestine = 'TreasureID', 'TreasureName', 'FellowID', 'PredestineName', 'PredestineDesc'
sql_treasure_predestine   = 'SELECT %s FROM tb_treasure_predestine' % ','.join(field_treasure_predestine)
insert_sql_skill   = 'INSERT INTO tb_treasure_predestine (%s) VALUES (%s)' % (','.join(field_treasure_predestine), ','.join(['%s'] * len(field_treasure_predestine)))

IMPORT_SQLS = {
        'TreasurePredestine'   : [insert_sql_skill, 'tb_treasure_predestine'],
    }

EXPORT_SQLS = {
        'tb_treasure_predestine' : [sql_treasure_predestine, field_treasure_predestine, 'TreasurePredestine'],
    }

@route("/treasure_predestine")
def treasure_predestine_index(db):
    db.execute(sql_treasure_predestine)
    data = db.fetchall()
    return template('treasure_predestine_index', data=data)

@route("/treasure_predestine/delete", method="POST")
def treasure_predestine_delete(db):
    sid = request.forms.sid.strip()
    sql = 'DELETE FROM tb_treasure_predestine WHERE TreasureID=%s;' % sid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/treasure_predestine/import", method="POST")
def treasure_predestine_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS 

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmp_treasure_predestine%Y%m%d%H%M%S.xls'))
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
        redirect("/treasure_predestine")

@route("/treasure_predestine/export")
def treasure_predestine_export(db):
    tmp_root = './tmp/'
    filename = current_time("treasure_predestine_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/treasure_predestine/recover")
def treasure_predestine_recover(db):
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
        redirect('/treasure_predestine')

