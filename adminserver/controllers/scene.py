#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

SCENE_BACK_FILE = 'scene_back_up.xls'

field_scene = 'TownID', 'Name', 'AssectPath', 'Path', 'BGMusic', 'LowLevel', 'PreposeScene', 'StarNum', 'SceneDiff'
sql_scene = 'SELECT %s FROM tb_scene' % ','.join(field_scene)
insert_sql = 'INSERT INTO tb_scene VALUES (%s)' % ','.join(['%s'] * len(field_scene))

field_scene_dungeon = 'DungeonID', 'Turn', 'Name', 'Path', 'PosX', 'PosY', 'Type', 'StoryID', 'RushMax', 'TownID', 'DropList', 'WorldDropID', 'AwardList'
sql_scene_dungeon   = 'SELECT %s FROM tb_scene_dungeon' % ','.join(field_scene_dungeon)
insert_sql_dungeon  = 'INSERT INTO tb_scene_dungeon VALUES (%s)' % ','.join(['%s'] * len(field_scene_dungeon))

field_scene_reward  = 'TownID', 'StarCount', 'Reward'
sql_scene_reward    = 'SELECT %s FROM tb_scene_star_reward' % ','.join(field_scene_reward)
insert_sql_reward   = 'INSERT INTO tb_scene_star_reward VALUES (%s)' % ','.join(['%s'] * len(field_scene_reward))


SCENE_IMPORT_SQLS = {
        'Scene'     : [insert_sql, 'tb_scene'],  # 若目录tmp_root不存在，则创建
        'Dungeon'   :[insert_sql_dungeon, 'tb_scene_dungeon'],
        'StarReward':[insert_sql_reward, 'tb_scene_star_reward'],
    }

SCENE_EXPORT_SQLS = {
        'tb_scene'            : [sql_scene, field_scene, 'Scene'],
        'tb_scene_dungeon'    : [sql_scene_dungeon, field_scene_dungeon, 'Dungeon'],
        'tb_scene_star_reward': [sql_scene_reward, field_scene_reward, 'StarReward'],
    }


@route("/scene")
def scene_index(db):
    db.execute(sql_scene)
    data = db.fetchall()
    '''
    db.execute(sql_scene_dungeon)
    dungeons = db.fetchall()
    db.execute(sql_scene_reward)
    rewards = db.fetchall()
    '''
    return template('scene_index', data=data)
    #return template('scene_index', data=data, dungeons=dungeons, rewards=rewards)

@route("/scene/delete", method="POST")
def scene_delete(db):
    sid = request.forms.sid.strip()
    sql = 'DELETE FROM tb_scene WHERE TownID=%s;' % sid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/scene/import", method="POST")
def scene_import(db):
    data = request.files.data
    error = ''
    all_sqls = SCENE_IMPORT_SQLS

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpscene_%Y%m%d%H%M%S.xls'))
        tmp_file = open(tmp_filename, 'w') # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件中
        rows = data.file.readlines()

        if not rows: # 文件空 
            error = '数据格式错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 在导入新的数据前，先将数据库原有数据导出到tmp目录，作为备份，数据导入失败时可以恢复数据
        export_sqls = SCENE_EXPORT_SQLS
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
        redirect("/scene")

@route("/scene/export")
def scene_export(db):
    tmp_root = './tmp/'
    filename = current_time("scene_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = SCENE_EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/scene/recover")
def scene_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, SCENE_BACK_FILE)
    error = ''
    if not isfile(filename):
        error = '没有备份文件'
        return template('error', error=error)
    all_sqls = SCENE_IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error= '数据恢复失败，原因：' + error)
    else:
        redirect('/scene')

@route("/scene/dungeon/get", method="POST")
def scene_dungeon_get(db):
    sid = request.forms.sid.strip()
    db.execute('SELECT DungeonID,Turn,Name,Path,PosX,PosY,Type,StoryID,RushMax,DropList,WorldDropID,AwardList FROM tb_scene_dungeon WHERE TownID=%s', (sid, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}
 
@route("/scene/reward/get", method="POST")
def scene_reward_get(db):
    sid = request.forms.sid.strip()
    db.execute('SELECT StarCount,Reward FROM tb_scene_star_reward WHERE TownID=%s', (sid, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}
 
@route("/scene/deldungeon", method="POST")
def scene_dungeon_delete(db):
    sid     = request.forms.sid.strip()
    dung_id = request.forms.dung_id.strip()
    db.execute('DELETE FROM tb_scene_dungeon WHERE DungeonID=%s AND TownID=%s', (dung_id, sid))
    return {'result': 0, 'data':''}
  
@route("/scene/delreward", method="POST")
def scene_reward_delete(db):
    sid        = request.forms.sid.strip()
    star_count = request.forms.star_count.strip()
    db.execute('DELETE FROM tb_scene_reward WHERE TownID=%s AND StarCount=%s', (sid, star_count))
    return {'result': 0, 'data':''}
    
