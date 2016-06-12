#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'dialogue_back_up.xls'

field_dialogue = 'DialogueGroup', 'DialogueID', 'DialogueType', 'SceneID', 'DungeonID', 'DungeonDiff', 'MonsterRound', 'MonsterTurn', 'MonsterID', 'Life', 'MonsterDied', 'Win', 'IsMark'
sql_dialogue   = 'SELECT %s FROM tb_dialogue' % ','.join(field_dialogue)
insert_sql     = 'INSERT INTO tb_dialogue VALUES (%s)' % ','.join(['%s'] * len(field_dialogue))

field_dialogue_content = 'DialogueID', 'DialogueTurn', 'NPC', 'NPCName', 'NPCPosition', 'NPCIcon', 'IconPositionX', 'IconPositionY', 'DialogueContent', 'IsChangeScene', 'IsChangeMusic', 'ChangeBattleArrayType', 'MonsterID', 'MonsterAttributeID', 'IsVictory'
sql_dialogue_content   = 'SELECT %s FROM tb_dialogue_content' % ','.join(field_dialogue_content)
insert_sql_content     = 'INSERT INTO tb_dialogue_content (%s) VALUES (%s)' % (','.join(field_dialogue_content), ','.join(['%s'] * len(field_dialogue_content)))
select_sql_content     = 'SELECT %s FROM tb_dialogue_content WHERE DialogueID=%s'

IMPORT_SQLS = {
        'Dialogue'        : [insert_sql        , 'tb_dialogue'],  # 第二个元素为数据表名
        'DialogueContent' : [insert_sql_content, 'tb_dialogue_content'],
    }

EXPORT_SQLS = {
        'tb_dialogue'         : [sql_dialogue        , field_dialogue        , 'Dialogue'],
        'tb_dialogue_content' : [sql_dialogue_content, field_dialogue_content, 'DialogueContent'],
    }

@route("/dialogue")
def dialogue_index(db):
    db.execute(sql_dialogue)
    data = db.fetchall()
    return template('dialogue_index', data=data)

@route("/dialogue/delete", method="POST")
def dialogue_delete(db):
    mid = request.forms.mid.strip()
    sql = 'DELETE FROM tb_dialogue WHERE DialogueID=%s;' % mid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/dialogue/import", method="POST")
def dialogue_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS 

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpdialogue_%Y%m%d%H%M%S.xls'))
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
        redirect("/dialogue")

@route("/dialogue/export")
def dialogue_export(db):
    tmp_root = './tmp/'
    filename = current_time("dialogue_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/dialogue/recover")
def dialogue_recover(db):
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
        redirect('/dialogue')

@route("/dialogue/content/get", method="POST")
def dialogue_content_get(db):
    mid = request.forms.mid.strip()
    #db.execute('SELECT DialogueID, DialogueTurn, NPC, NPCName, NPCPosition, NPCIcon, IconPositionX, IconPositionY, DialogueContent, IsChangeScene, IsChangeMusic, ChangeBattleArrayType, MonsterID, MonsterAttributeID, IsVictory FROM tb_dialogue_content WHERE DialogueID=%s', (mid,))
    db.execute(select_sql_content%( ','.join(field_dialogue_content), mid ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}

@route("/dialogue/delcontent", method="POST")
def dialogue_content_delete(db):
    turn_id = request.forms.turn_id.strip()
    db.execute('DELETE FROM tb_dialogue_content WHERE DialogueTurn=%s', (turn_id, ))
    return {'result': 0, 'data':''}
 


