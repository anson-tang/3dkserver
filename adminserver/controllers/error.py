#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from bottle_mysql import MySQLPlugin
from utils import current_time
from os.path import isfile, isdir
import os
from excel import excel_import, excel_export


# import sql
sql_error = 'INSERT INTO tb_error VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
ERROR_IMPORT_SQLS = {'tb_error': [sql_error, [5,]],
                      }

# export sql include tb_keyword
sql_error = 'SELECT err_id,err_number,err_type,button_type,need_reboot,tb_keyword.inter_value\
        ,jump_1,jump_2,jump_3,asset_id FROM tb_error LEFT JOIN tb_keyword ON tb_error.err_desc=tb_keyword.inter_key '
title_error = 'err_id,err_number,err_type,button_type,need_reboot,err_desc,jump_1,jump_2,jump_3,asset_id'
ERROR_EXPORT_SQLS = {'tb_error': [sql_error, title_error],
                   }

ERROR_BACK_FILE = 'error_back_up.xls'

@route("/errorCode")
def error_index(db, cur_page=0):
    #data    = db.select("SELECT * FROM tb_error;");
    data = db.select(sql_error)
    return template('error_index', data=data)

@route("/error/new")
def error_new():
    error = ('', '', '', '', '', '', '', '', '', '') 
    return template('error_detail', error=error, new=1)

@route("/error/edit/<eid:int>")
def error_edit(eid, db):
    sql = sql_error + ' WHERE err_id=%d' % eid
    the_error = db.select_one(sql)
    return template('error_detail', error=the_error, new=0)

@route("/error/save", method="POST")
def error_save(db):
    eid         = request.forms.eid.strip()
    err_number  = request.forms.err_number.strip()
    err_type    = request.forms.err_type.strip()
    button_type = request.forms.button_type.strip()
    need_reboot = request.forms.need_reboot.strip()
    err_desc    = request.forms.err_desc.strip()
    jump_1      = request.forms.jump_1.strip()
    jump_2      = request.forms.jump_2.strip()
    jump_3      = request.forms.jump_3.strip()
    asset_id    = request.forms.asset_id.strip()
    _new         = int(request.forms.e_new)

    inter_contents = ['tb_error.err_desc.%s' %eid, err_desc]

    if not _new:
        sql = 'UPDATE tb_error SET err_id=%s,err_number=%s,err_type=%s,button_type=%s,need_reboot=%s,err_desc="%s"\
                , jump_1=%s,jump_2=%s,jump_3=%s,asset_id=%s WHERE err_id=%s;' % (eid,err_number, err_type, button_type\
                        , need_reboot, inter_contents[0], jump_1, jump_2, jump_3, asset_id, eid)
        db.update(sql)

        # international数据表更新 
        try:
            inter_sql = 'UPDATE tb_keyword SET inter_value="%s" WHERE inter_key="%s"' % (inter_contents[1], inter_contents[0])
            db.update(inter_sql)
        except Exception, e:
            print 'update error inter error : %s' %e
    else:
        sql = 'INSERT INTO tb_error \
                (err_id, err_number, err_type, button_type, need_reboot, err_desc, jump_1, jump_2, jump_3) \
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
        db.insert(sql, (eid, err_number, err_type, button_type, need_reboot, inter_contents[0], jump_1, jump_2, jump_3, asset_id))

        # international数据表
        try:
            inter_sql = 'INSERT INTO tb_keyword VALUES (%s,%s)'
            db.insert(inter_sql, inter_contents)
        except Exception, e:
            print 'insert error inter error : %s' %e

    redirect("/errorCode")

@route("/error/delete", method="POST")
def error_delete(db):
    eid = request.forms.eid.strip()
    sql = 'DELETE FROM tb_error WHERE err_id=%s;' % eid
    inter_key = 'tb_error.err_desc.%s'%eid
    try:
        db.delete(sql)
        inter_sql = 'DELETE FROM tb_keyword WHERE inter_key="%s"' %inter_key
        db.delete(inter_sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/error/import", method="POST")
def error_import(db):
    data = request.files.data
    error = ''
    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmperror_%Y%m%d%H%M.xls'))
        tmp_file = open(tmp_filename, 'w')  # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件
        rows = data.file.readlines()
        if not rows:  # 文件空
            error = '数据个数错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 导入数据前，先对数据库数据进行备份
        export_sqls = ERROR_EXPORT_SQLS
        try:
            # 若备份文件存在，删除重新写入
            if os.path.exists(os.path.join(tmp_root, ERROR_BACK_FILE)):
                os.remove(os.path.join(tmp_root, ERROR_BACK_FILE))
            excel_export(export_sqls, tmp_root, ERROR_BACK_FILE, db)
        except Exception, e:
            print 'error 数据备份错误: %s' %e

        all_sqls = ERROR_IMPORT_SQLS
        error = excel_import(all_sqls, tmp_filename, db)
        os.remove(tmp_filename)  # 删除临时文件

    else:
        error = '数据格式错误[1]'

    if error:
        # 导入数据错误，进行数据恢复 
        try:
            excel_import(all_sqls, os.path.join(tmp_root, ERROR_BACK_FILE), db)
            print 'error 数据恢复成功'
        except Exception, e:
            print 'error 数据恢复错误: %s' %e
        return template('error', error=error + '  数据已恢复')
    else:
        redirect("/errorCode")

@route("/error/export")
def error_export(db):
    tmp_root = './tmp/'
    filename = current_time("error_%Y%m%d%H%M.xls")
    error = ''

    if not isfile(tmp_root + filename):
        all_sqls = ERROR_EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/error/recover")
def error_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, ERROR_BACK_FILE)
    error =''
    if not isfile(filename):
        error = '没有error备份文件'
        return template('error', error=error)
    all_sqls = ERROR_IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error = '数据恢复失败，原因：' + error)
    else:
        redirect('/errorCode')


