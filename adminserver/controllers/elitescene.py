#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

SCENE_BACK_FILE = 'elitescene_back_up.xls'

field_elitescene = 'SceneID', 'EliteSceneID', 'PrepEliteSceneID', 'EliteSceneName', 'MonsterIcon', 'EliteSceneBG', 'FightBG', 'BGMusic', 'NeedRoleLevel', 'Gold', 'Soul', 'RewardList'
sql_elitescene   = 'SELECT %s FROM tb_elitescene' % ','.join(field_elitescene)
insert_sql       = 'INSERT INTO tb_elitescene VALUES (%s)' % ','.join(['%s'] * len(field_elitescene))

field_elitescene_monster      = 'EliteSceneID', 'Turn', 'IsBoss', 'MonsterList', 'MonsterAttrList'
sql_elitescene_monster        = 'SELECT %s FROM tb_elitescene_monster' % ','.join(field_elitescene_monster)
insert_sql_elitescene_monster = 'INSERT INTO tb_elitescene_monster VALUES (%s)' % ','.join(['%s'] * len(field_elitescene_monster))
get_elitescene_monster        = 'SELECT %s FROM tb_elitescene_monster WHERE EliteSceneID=%s'
#get_elitescene_monster        = 'SELECT EliteSceneID,Turn,MonsterList,MonsterAttrList FROM tb_elitescene_monster WHERE EliteSceneID=%s'

excel_name = 'EliteScene'
sub_excel_name = 'EliteSceneMonster'
excel_export_filename = "EliteScene_%Y%m%d%H%M.xls"

IMPORT_SQLS = {
        excel_name  : [insert_sql, 'tb_elitescene'],  # 若目录tmp_root不存在，则创建
    sub_excel_name  :[insert_sql_elitescene_monster, 'tb_elitescene_monster'],
    }

EXPORT_SQLS = {
        'tb_elitescene'            : [sql_elitescene, field_elitescene, excel_name],
        'tb_elitescene_monster'    : [sql_elitescene_monster, field_elitescene_monster, sub_excel_name],
    }


@route("/elitescene")
def elitescene_index(db):
    db.execute(sql_elitescene)
    data = db.fetchall()
    return template('elitescene_index', data=data)

@route("/elitescene/delete", method="POST")
def elitescene_delete(db):
    sid = request.forms.sid.strip()
    sql = 'DELETE FROM tb_elitescene WHERE EliteSceneID=%s;' % sid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/elitescene/import", method="POST")
def elitescene_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpelitescene_%Y%m%d%H%M%S.xls'))
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
        redirect("/elitescene")

@route("/elitescene/export")
def elitescene_export(db):
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

@route("/elitescene/recover")
def elitescene_recover(db):
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
        redirect('/elitescene')

@route("/elitescene/monster/get", method="POST")
def elitescene_monster_get(db):
    sid = request.forms.sid.strip()
    #db.execute('SELECT Turn,MonsterList,MonsterAttrList FROM tb_elitescene_monster WHERE EliteSceneID=%s', (sid, ))
    db.execute( get_elitescene_monster % (','.join(field_elitescene_monster[1:]), sid))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}
 
@route("/elitescene/delmonster", method="POST")
def elitescene_monster_del(db):
    sid = request.forms.sid.strip()
    tid = request.forms.tid.strip()
    db.execute('DELETE FROM tb_elitescene_monster WHERE EliteSceneID=%s AND Turn=%s', (sid, tid))
    return {'result': 0, 'data':''}
  
    
