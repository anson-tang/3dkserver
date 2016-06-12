#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from util   import current_time
from os.path import isfile, isdir
import os
import sys
from excel import excel_import, excel_export
from utils import pprint

BACK_FILE = 'fellow_back_up.xls'
TABLE_NAME = 'tb_fellow'

field_base = 'FellowID', 'Name', 'FellowDesc', 'Scale', 'NameX', 'NameY', 'Star', 'Quality', 'QualityLevel', \
        'FellowType', 'IsSingle', 'Level', 'Exp', 'AdvancedCount', 'ChangeFellow', 'ResGroup', 'Path', 'IconPath', \
        'Camp', 'Priority', 'AttackID', 'AttackName', 'AttackDesc', 'SkillID', 'SkillName', \
        'SkillDesc', 'IdleSound', 'AttackSound', 'SkillSound', 'HurtSound', 'TalkSound', 'Physical', \
        'Magic', 'MCurrentLife', 'MMaxLife', 'IncreasedLife', \
        'MCurrentMana', 'AttackType', 'Attack', 'IncreasedAttack', 'PhysicsDefense', \
        'IncreasedPhysicsDefense', 'MagicDefense', 'IncreasedMagicDefense', 'Crit', \
        'CritResistance', 'CritDamage', 'CritDamageReduction', 'Block', 'BlockResistance', \
        'Counter', 'CounterResistance', 'Accurate', 'Miss'
sql_base = 'SELECT %s FROM %s' % (','.join(field_base), TABLE_NAME)
insert_sql = 'INSERT INTO %s VALUES (%s)' % (TABLE_NAME, ','.join(['%s'] * len(field_base)))

field_decomposition      = 'QualityLevel', 'ItemList'
sql_decomposition        = 'SELECT %s FROM tb_fellow_decomposition' % ','.join(field_decomposition)
insert_sql_decomposition = 'INSERT INTO tb_fellow_decomposition VALUES (%s)' % ','.join(['%s'] * len(field_decomposition))

field_reborn      = 'QualityLevel', 'AdvancedCount', 'Cost'
sql_reborn        = 'SELECT %s FROM tb_fellow_reborn' % ','.join(field_reborn)
insert_sql_reborn = 'INSERT INTO tb_fellow_reborn VALUES (%s)' % ','.join(['%s'] * len(field_reborn))


IMPORT_SQLS = {
        'Fellow'              : [insert_sql, 'tb_fellow'],  # 第二个元素为数据表名
        'FellowDecomposition' : [insert_sql_decomposition, 'tb_fellow_decomposition'],
        'FellowReborn'        : [insert_sql_reborn, 'tb_fellow_reborn'],
    }

EXPORT_SQLS = {
        'tb_fellow'               : [sql_base, field_base, 'Fellow'],
        'tb_fellow_decomposition' : [sql_decomposition, field_decomposition, 'FellowDecomposition'],
        'tb_fellow_reborn'        : [sql_reborn, field_reborn, 'FellowReborn'],
    }


@route("/fellow")
def fellow_index(db):
    db.execute(sql_base)
    data = db.fetchall()
    return template('fellow_index', data=data)

@route("/fellow/delete", method="POST")
def fellow_delete(db):
    sid = request.forms.fid.strip()
    sql = 'DELETE FROM tb_fellow WHERE FellowID=%s;' % fid

    try:
        db.execute(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/fellow/import", method="POST")
def fellow_import(db):
    data = request.files.data
    error = ''
    all_sqls = IMPORT_SQLS

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpfellow_%Y%m%d%H%M%S.xls'))
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
        redirect("/fellow")

@route("/fellow/export")
def fellow_export(db):
    tmp_root = './tmp/'
    filename = current_time("fellow_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)

@route("/fellow/recover")
def fellow_recover(db):
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
        redirect('/fellow')

@route("/fellow/decomposition/get", method="POST")
def fellow_decomposition_get(db):
    qlevel = request.forms.qlevel.strip()
    db.execute('{0} WHERE QualityLevel=%s'.format(sql_decomposition), (qlevel, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}

@route("/fellow/reborn/get", method="POST")
def fellow_reborn_get(db):
    qlevel = request.forms.qlevel.strip()
    db.execute('{0} WHERE QualityLevel=%s'.format(sql_reborn), (qlevel, ))
    _data = db.fetchall()
    return {'result': 0 if len(_data) > 0 else 1, 'data':_data}

@route("/fellow/deldecomposition", method="POST")
def fellow_decomposition_delete(db):
    qlevel = request.forms.qlevel.strip()
    db.execute('DELETE FROM tb_fellow_decomposition WHERE QualityLevel=%s', (qlevel, ))
    return {'result': 0, 'data':''}

@route("/fellow/delreborn", method="POST")
def fellow_reborn_delete(db):
    qlevel = request.forms.qlevel.strip()
    db.execute('DELETE FROM tb_fellow_reborn WHERE QualityLevel=%s', (qlevel, ))
    return {'result': 0, 'data':''}
 
