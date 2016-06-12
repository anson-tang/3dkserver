#-*-coding:utf-8-*-

from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'task_back_up.xls'
table_name = 'tb_task'
field_base = 'ID', 'Name', 'PreTask', 'LowerestLevel', 'HighestLevel', 'StartNPCID', 'StartNPCX', 'StartNPCY', 'FinishNPCID', \
        'FinishNPCX', 'FinishNPCY', 'NeedPassDungeon', 'RewardList'
sql_base = 'SELECT %s FROM %s' % (','.join(field_base), table_name)
insert_sql = 'INSERT INTO %s VALUES (%s)' % (table_name, ','.join(['%s'] * len(field_base)))

field_dialogue = 'ID', 'TaskID', 'Type', 'Turn', 'NPC', 'Path', 'ICON', 'Dialogue'
sql_dialogue   = 'SELECT %s FROM tb_task_dialogue' % ','.join(field_dialogue)
insert_sql_dialogue = 'INSERT INTO tb_task_dialogue (%s) VALUES (%s)' % (','.join(field_dialogue[1:]), ','.join(['%s'] * (len(field_dialogue)-1)))

field_dungeon  = 'ID', 'TaskID', 'Type', 'Value', 'Turn', 'NPC', 'Path', 'ICON', 'Dialogue'
sql_dungeon = 'SELECT %s FROM tb_task_dungeon' % ','.join(field_dungeon)
insert_sql_dungeon = 'INSERT INTO tb_task_dungeon (%s) VALUES (%s)' % (','.join(field_dungeon[1:]), ','.join(['%s'] * (len(field_dungeon)-1)))


IMPORT_SQLS = {
        'Task'     : [insert_sql, 'tb_task'],  # 第二个元素为数据表名
        'Dialogue'   :[insert_sql_dialogue, 'tb_task_dialogue'],
        'Dungeon_Dialogue':[insert_sql_dungeon, 'tb_task_dungeon'],
    }

EXPORT_SQLS = {
        'tb_task'          : [sql_base, field_base, 'Task'],
        'tb_task_dialogue' : [sql_dialogue, field_dialogue, 'Dialogue'],
        'tb_task_dungeon'  : [sql_dungeon, field_dungeon, 'Dungeon_Dialogue'],
    }


@route("/task")
def task_index(db):
    db.execute(sql_base)
    data = db.fetchall()
    return template('task_index', data=data)

@route("/task/delete", method="POST")
def task_delete(db):
    sid = request.forms.tid.strip()
    sql = 'DELETE FROM tb_task WHERE ID=%s;' % tid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/task/import", method="POST")
def task_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmptask_%Y%m%d%H%M%S.xls'))
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
        redirect("/task")

@route("/task/export")
def task_export(db):
    tmp_root = './tmp/'
    filename = current_time("task_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/task/recover")
def task_recover(db):
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
        redirect('/task')

@route("/task/dialogue/get", method="POST")
def task_dialogue_get(db):
    tid = request.forms.tid.strip()
    db.execute('%s WHERE TaskID=%s' % (sql_dialogue, tid))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}
 
@route("/task/dungeon/get", method="POST")
def task_dungeon_get(db):
    tid = request.forms.tid.strip()
    db.execute('%s WHERE TaskID=%s' % (sql_dungeon, tid))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}
 
@route("/task/deldungeon", method="POST")
def task_dungeon_delete(db):
    tid     = request.forms.tid.strip()
    dung_id = request.forms.dung_id.strip()
    db.execute('DELETE FROM tb_task_dungeon WHERE ID=%s AND TaskID=%s', (dung_id, tid))
    return {'result': 0, 'data':''}
  
@route("/task/deldialogue", method="POST")
def task_dialogue_delete(db):
    tid        = request.forms.tid.strip()
    dialog_id  = request.forms.dialog_id.strip()
    db.execute('DELETE FROM tb_task_dialogue WHERE TaskID=%s AND ID=%s', (tid, dialog_id))
    return {'result': 0, 'data':''}
     
