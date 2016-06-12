#-*-coding:utf-8-*-
from bottle import route, request, template, redirect, static_file
from bottle_mysql import MySQLPlugin
from utils import current_time
from os.path import isfile, isdir
import os
import sys
import xlrd, xlwt
from excel import excel_import, excel_export

def uprint(o):
    sys.stderr.write(str(o) + '\n')

SOLDIER_TYPE     = ('', '骑兵', '步兵', '弓箭兵', '运输兵', '城防骑兵', '城防步兵', '城防弓箭兵')
SOLDIER_QUANTITY = ('', '一星', '二星', '三星', '四星')
SOLDIER_RACE     = ('', '人族', '吸血鬼', '狼人', 'NPC')

# import sql
sql_soldier = 'INSERT INTO tb_soldier VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
sql_soldier_recruit_limit = 'INSERT INTO tb_soldier_recruit_limit VALUES (%s,%s,%s)'
SOLDIER_IMPORT_SQLS = {'tb_soldier': [sql_soldier, [4, 5]],  # 第二个元素为类型为字符的列数的list 
                       'tb_soldier_recruit_limit': [sql_soldier_recruit_limit, []], 
                      }
# export sql
#sql_soldier = 'SELECT soldier_id,soldier_type_id,soldier_quantity,soldier_race,soldier_name,\
#        soldier_description,asset_id,food_need,wood_need,stone_need,ore_need,recruit_time,food_per_hour,\
#        population_need,attack,hp,might,attack_level,hp_level,res_carry,move_rate FROM tb_soldier'
#sql_recruit_limit = 'SELECT soldier_id, limit_type_id, limit_value FROM tb_soldier_recruit_limit'
#sql_recruit_limit_type = 'SELECT limit_type_id, limit_type FROM tb_limit_type'

# new export sql include tb_keyword
sql_soldier = 'SELECT soldier_id,soldier_type_id,soldier_quantity,soldier_race,tb_soldier_name.inter_value,\
        tb_soldier_description.inter_value,asset_id,food_need,wood_need,stone_need,ore_need,recruit_time,food_per_hour,\
        population_need,attack,hp,might,attack_level,hp_level,res_carry,move_rate,sort_order,scores FROM tb_soldier \
        LEFT JOIN tb_keyword AS tb_soldier_name ON tb_soldier.soldier_name=tb_soldier_name.inter_key \
        LEFT JOIN tb_keyword AS tb_soldier_description ON tb_soldier.soldier_description=tb_soldier_description.inter_key'
sql_recruit_limit = 'SELECT soldier_id, limit_type_id, limit_value FROM tb_soldier_recruit_limit'
sql_recruit_limit_type = 'SELECT limit_type_id, limit_type FROM tb_limit_type'
title_soldier = 'soldier_id,soldier_type_id,soldier_quantity,soldier_race,soldier_name,\
        soldier_description,asset_id,food_need,wood_need,stone_need,ore_need,recruit_time,food_per_hour,\
        population_need,attack,hp,might,attack_level,hp_level,res_carry,move_rate,sort_order,scores'
title_recruit_limit = 'soldier_id, limit_type_id, limit_value'
title_recruit_limit_type = 'limit_type_id, limit_type'  
SOLDIER_EXPORT_SQLS = {'tb_soldier': [sql_soldier, title_soldier],
                       'tb_soldier_recruit_limit': [sql_recruit_limit, title_recruit_limit],
                      }

SOLDIER_BACK_FILE = 'soldier_back_up.xls'

insert_soldier_restrain = 'INSERT INTO tb_soldier_restrain VALUES (%s,%s,%s)'
SOLDIER_RESTRAIN_IMPORT_SQLS = {'tb_soldier_restrain': [insert_soldier_restrain, []]}

select_soldier_restrain = 'SELECT soldier_id,restrain_soldier_id,restrain_value FROM tb_soldier_restrain'
title_soldier_restrain = 'soldier_id,restrain_soldier_id,restrain_value'
SOLDIER_RESTRAIN_EXPORT_SQLS = {'tb_soldier_restrain': [select_soldier_restrain, title_soldier_restrain]}

SOLDIER_RESTRAIN_BACK_FILE = 'soldier_restrain_back_up.xls'

@route("/soldier")
def soldier_index(db):
    #data   = db.select("SELECT * FROM tb_soldier;");
    data = db.select(sql_soldier)
    #limits = db.select("SELECT * FROM tb_limit_type;");
    limits = db.select("SELECT limit_type_id,inter_value from tb_limit_type LEFT JOIN tb_keyword ON\
            tb_limit_type.limit_type=tb_keyword.inter_key")
    return template('soldier_index', data=data, 
                                     stype=SOLDIER_TYPE,
                                     quantity=SOLDIER_QUANTITY,
                                     limits=limits,
                                     srace=SOLDIER_RACE)

@route("/soldier/all")
def soldier_all(db):
    all_result = db.select("SELECT soldier_id,soldier_type_id,soldier_quantity,soldier_name FROM tb_soldier;");
    return {'result':0, 'data':all_result}

@route("/soldier/common/all")
def soldier_all(db):
    all_result = db.select("SELECT soldier_id,soldier_type_id,soldier_quantity,soldier_name FROM tb_soldier WHERE soldier_type_id<5;");
    return {'result':0, 'data':all_result}

@route("/soldier/wall/all")
def soldier_wall_all(db):
    all_result = db.select("SELECT soldier_id,soldier_type_id,soldier_quantity,soldier_name FROM tb_soldier WHERE soldier_type_id>4;");
    return {'result':0, 'data':all_result}

@route("/soldier/new")
def soldier_new():
    soldier = ('', ) * 23 #0, 0, 0, '', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    return template('soldier_detail', soldier=soldier, new=1,
                                     stype=SOLDIER_TYPE[1:],
                                     quantity=SOLDIER_QUANTITY[1:],
                                     srace=SOLDIER_RACE[1:])

@route("/soldier/edit/<sid:int>")
def soldier_edit(sid, db):
    sql = sql_soldier + ' WHERE soldier_id=%d' % sid
    the_soldier = db.select_one(sql)
    uprint(the_soldier)
    return template('soldier_detail', soldier=the_soldier, new=0,
                                     stype=SOLDIER_TYPE[1:],
                                     quantity=SOLDIER_QUANTITY[1:],
                                     srace=SOLDIER_RACE[1:])

@route("/soldier/save", method="POST")
def soldier_save(db):
    sid        = request.forms.sid.strip()
    s_type_id  = request.forms.s_type_id.strip()
    s_quantity = request.forms.s_quantity.strip()
    s_race     = request.forms.s_race.strip()
    s_name     = request.forms.s_name.strip()
    s_desc     = request.forms.s_desc.strip()
    s_asset_id = request.forms.s_asset_id.strip()
    s_food_need       = request.forms.s_food_need.strip()
    s_wood_need       = request.forms.s_wood_need.strip()
    s_stone_need      = request.forms.s_stone_need.strip()
    s_ore_need        = request.forms.s_ore_need.strip()
    s_recruit_time    = request.forms.s_recruit_time.strip()
    s_food_per_hour   = request.forms.s_food_per_hour.strip()
    s_population_need = request.forms.s_population_need.strip()
    s_attack       = request.forms.s_attack.strip()
    s_hp           = request.forms.s_hp.strip()
    s_might        = request.forms.s_might.strip()
    s_attack_level = request.forms.s_attack_level.strip()
    s_hp_level     = request.forms.s_hp_level.strip()
    s_res_carry    = request.forms.s_res_carry.strip()
    s_move_rate    = request.forms.s_move_rate.strip()
    s_sort_order   = request.forms.s_sort_order.strip()
    s_scores       = request.forms.s_scores.strip()

    _new           = int(request.forms.s_new)


    inter_contents = [['tb_soldier.soldier_name.%s' %sid.strip(), s_name], ['tb_soldier.soldier_description.%s' %sid.strip(), s_desc]]

    if not _new:
        sql = 'UPDATE tb_soldier SET soldier_id=%s,soldier_type_id=%s,soldier_quantity=%s,soldier_race=%s,soldier_name="%s",\
                soldier_description="%s",asset_id=%s,food_need=%s,wood_need=%s,stone_need=%s,ore_need=%s,recruit_time=%s,\
                food_per_hour=%s,population_need=%s,attack=%s,hp=%s,might=%s,attack_level=%s,hp_level=%s,\
                res_carry=%s,move_rate=%s,sort_order=%s,scores=%s WHERE soldier_id=%s;' % (\
                    sid, s_type_id, s_quantity, s_race, inter_contents[0][0], inter_contents[1][0],
                    s_asset_id, s_food_need, s_wood_need, s_stone_need, s_ore_need, s_recruit_time, s_food_per_hour,
                    s_population_need, s_attack, s_hp, s_might, s_attack_level, s_hp_level, s_res_carry, s_move_rate, \
                    s_sort_order, s_scores, sid)
        db.update(sql)

        # keyword数据表更新
        for inter in inter_contents:
            try:
                inter_sql = 'UPDATE tb_keyword SET inter_value="%s" WHERE inter_key="%s"' % (inter[1], inter[0])
                db.update(inter_sql)
            except Exception, e:
                print 'update soldier inter error : %s' %e
    else:
        sql = 'INSERT INTO tb_soldier (soldier_id,soldier_type_id,soldier_quantity,soldier_race,soldier_name,\
                soldier_description,asset_id,food_need,wood_need,stone_need,ore_need,recruit_time,food_per_hour,\
                population_need,attack,hp,might,attack_level,hp_level,res_carry,move_rate,sort_order,scores) VALUES (\
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
        db.insert(sql, (sid, s_type_id, s_quantity, s_race, inter_contents[0][0], inter_contents[1][0],
                    s_asset_id, s_food_need, s_wood_need, s_stone_need, s_ore_need, s_recruit_time, s_food_per_hour,
                    s_population_need, s_attack, s_hp, s_might, s_attack_level, s_hp_level, s_res_carry, \
                    s_move_rate,s_sort_order,s_scores))
        # keyword数据表
        try:
            inter_sql = 'INSERT INTO tb_keyword VALUES (%s,%s)'
            db.insert(inter_sql, inter_contents)
        except Exception, e:
            print 'insert soldier inter error : %s' %e

    redirect("/soldier")

@route("/soldier/delete", method="POST")
def soldier_delete(db):
    sid = request.forms.sid.strip()
    sql = 'DELETE FROM tb_soldier WHERE soldier_id=%s;' % sid
    inter_keys = ['tb_soldier.soldier_name.%s'%sid, 'tb_soldier.soldier_description.%s'%sid]
    try:
        db.delete(sql)
        for inter_key in inter_keys:
            inter_sql = 'DELETE FROM tb_keyword WHERE inter_key="%s"' % inter_key
            db.delete(inter_sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/soldier/import", method="POST")
def soldier_import(db):
    data = request.files.data
    error = ''

    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpsoldier_%Y%m%d%H%M%S.xls'))
        tmp_file = open(tmp_filename, 'w')  # 新建一个xls后缀的文件，然后将读取的excel文件的内容写入该文件中
        rows = data.file.readlines()

        if not rows:  # 文件空
            error = '数据格式错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()

        # 在导入新的数据前，先将数据库原有数据导出到tmp目录，作为备份，数据导入失败时可以恢复数据
        export_sqls = SOLDIER_EXPORT_SQLS
        try:
            # 若备份文件已存在，则删除重新写入
            if os.path.exists(os.path.join(tmp_root, SOLDIER_BACK_FILE)):
                os.remove(os.path.join(tmp_root, SOLDIER_BACK_FILE))
            excel_export(export_sqls, tmp_root, SOLDIER_BACK_FILE, db)
        except Exception, e:
            print 'soldier 数据备份错误: %s' %e

        all_sqls = SOLDIER_IMPORT_SQLS

        error = excel_import(all_sqls, tmp_filename, db)
        os.remove(tmp_filename)  # 删除上传的临时文件
    else:  # 没有文件
        error = '数据格式错误[1]'

    if error:
        # 导入数据错误，进行数据恢复
        try:
            excel_import(all_sqls, os.path.join(tmp_root, SOLDIER_BACK_FILE), db)
            print 'soldier 数据恢复成功'
        except Exception, e:
            print 'soldier 数据恢复错误: %s' %e
        return template('error', error=error + '    数据已恢复')
    else:
        redirect("/soldier")


def old_soldier_import(db):
    data = request.files.data
    error = ''

    if data and data.file:
        content = data.file.readlines()
        content = [[col.strip() for col in row.split(',')] for row in content[1:]]
        if content:
            try:
                db.delete('DELETE FROM tb_soldier;')
                sql = 'INSERT INTO tb_soldier VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                #for row in content[1:]:
                #    d = tuple([col.strip() for col in row.split(',')])
                #    sql += '(%s,"%s",%s,%s,%s,%s),' % d
                #sql = sql[:-1]

                #print sql
                db.insert(sql, content)
            except Exception, e:
                error = str(e)
        else:
            error = '数据格式错误[2]'
    else:
        error = '数据格式错误[1]'

    if error:
        return template('error', error=error)
    else:
        redirect("/soldier")

@route("/soldier/export")
def soldier_export(db):
    tmp_root = './tmp/'
    filename = current_time("soldier_%Y%m%d%H%M.xls")  # 文件名
    error = ''

    if not isfile(tmp_root + filename): 
        all_sqls = SOLDIER_EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:  
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)


def old_soldier_export(db):
    tmp_root = './tmp/'
    filename = current_time("soldier_%Y%m%d%H%M.csv")
    error = ''

    if not isfile(tmp_root + filename):

        sql = 'SELECT soldier_id,soldier_type_id,soldier_quantity,soldier_race,soldier_name,\
                soldier_description,asset_id,food_need,wood_need,stone_need,ore_need,recruit_time,food_per_hour,\
                population_need,attack,hp,might,attack_level,hp_level,res_carry,move_rate FROM tb_soldier'
        all_result = db.select(sql);

        csv = ['soldier_id,soldier_type_id,soldier_quantity,soldier_race,soldier_name,\
                soldier_description,asset_id,food_need,wood_need,stone_need,ore_need,recruit_time,food_per_hour,\
                population_need,attack,hp,might,attack_level,hp_level,res_carry,move_rate\n']
        for data in all_result:
            row = ','.join([str(data[0]).strip(), 
                            str(data[1]).strip(), 
                            str(data[2]).strip(), 
                            str(data[3]).strip(), 
                            str(data[4]).strip(), 
                            str(data[5]).strip(), 
                            str(data[6]).strip(), 
                            str(data[7]).strip(), 
                            str(data[8]).strip(), 
                            str(data[9]).strip(), 
                            str(data[10]).strip(), 
                            str(data[11]).strip(), 
                            str(data[12]).strip(), 
                            str(data[13]).strip(), 
                            str(data[14]).strip(), 
                            str(data[15]).strip(), 
                            str(data[16]).strip(), 
                            str(data[17]).strip(), 
                            str(data[18]).strip(), 
                            str(data[19]).strip(), 
                            str(data[20]).strip()])
            csv.append(row + '\n')

        if csv:
            try:
                file(tmp_root + filename, 'wb').writelines(csv)
            except Exception, e:
                error = str(e)

    if error:
        return template('error', error=error)
    else:
        return static_file(filename, root = tmp_root, download = filename)


@route("/soldier/recover")
def soldier_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, SOLDIER_BACK_FILE)
    error = ''
    if not isfile(filename):
        error = '没有soldier备份文件'
        return template('error', error=error)
    all_sqls = SOLDIER_IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error= '数据恢复失败，原因：' + error)
    else:
        redirect('/soldier')
    
@route("/soldier/fight")
def soldier_fight_simulator(db):
    stype = SOLDIER_TYPE[1:]
    quality = SOLDIER_QUANTITY[1:]
    race = SOLDIER_RACE[1:]
    
    return template('soldier_fight_simulator', stype=stype, quality=quality, race=race)

@route("/soldier/limit")
def soldier_limit_index(db):
    data = db.select("SELECT * FROM tb_limit_type;");
    return template('soldier_limit_index', data=data)

def _get_limits_by_sid(db, sid):
    data = db.select("SELECT tb_limit_type.limit_type_id,inter_value,limit_value\
            FROM tb_soldier_recruit_limit LEFT JOIN  tb_limit_type\
            ON tb_limit_type.limit_type_id=tb_soldier_recruit_limit.limit_type_id\
            LEFT JOIN tb_keyword ON tb_limit_type.limit_type=tb_keyword.inter_key\
            WHERE soldier_id=%s;" % sid);
    return data

@route("/soldier/limit/get", method="POST")
def soldier_limit_get(db):
    sid = request.forms.sid.strip()
    data = _get_limits_by_sid(db, sid)
    return {'result':0 if len(data) > 0 else 1, 'data':data}

@route("/soldier/newlimit", method="POST")
def soldier_newlimit(db):
    sid = request.forms.sid.strip()
    limit_type_id = request.forms.limit_type.strip()
    limit_value   = request.forms.limit_value.strip()
    if not sid:
        return {'result':1, 'data':'未选中士兵'}

    _sql = 'INSERT INTO tb_soldier_recruit_limit VALUES (%s,%s,%s);'
    db.insert(_sql, (sid, limit_type_id, limit_value))

    data = _get_limits_by_sid(db, sid)

    return {'result':0, 'data':data}

@route("/soldier/dellimit", method="POST")
def soldier_dellimit(db):
    sid = request.forms.sid.strip()
    lid = request.forms.lid.strip()
    value = request.forms.value.strip()
    if not sid:
        return {'result':1, 'data':'未选中士兵'}
    sql = 'DELETE FROM tb_soldier_recruit_limit WHERE soldier_id=%s AND limit_type_id=%s AND limit_value=%s;' % (sid, lid, value)
    print 'sql=', sql
    try:
        db.delete(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

'''
@route("/soldier/limit/save", method="POST")
def soldier_limit_save(db):
    l_type_id   = request.forms.limit_id.strip()
    l_type_name = request.forms.limit_type.strip()
    sql = 'INSERT INTO tb_limit_type VALUES (%s,%s)'
    db.insert(sql, (l_type_id, l_type_name))

    redirect("/soldier/limit")

@route("/soldier/limit/delete", method="POST")
def soldier_limit_delete(db):
    lid = request.forms.lid.strip()
    sql = 'DELETE FROM tb_limit_type WHERE limit_type_id=%s;' % lid
    print 'sql=', sql
    try:
        db.delete(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}
'''

@route("/soldier/restrain")
def soldier_restrain_index(db):
    data = db.select(select_soldier_restrain)
    soldiers = db.select('SELECT soldier_id, inter_value FROM tb_soldier LEFT JOIN tb_keyword \
            ON tb_keyword.inter_key=tb_soldier.soldier_name')
    return template("soldier_restrain_index", data=data, soldiers=soldiers)

@route("/soldier/restrain/save", method="POST")
def soldier_restrain_save(db):
    soldier_id = request.forms.soldier_id.strip()
    restrain_soldier_id = request.forms.restrain_soldier_id.strip()
    restrain_value = request.forms.restrain_value.strip()
    sql = 'INSERT INTO tb_soldier_restrain VALUES (%s,%s,%s)'
    db.insert(sql, (soldier_id, restrain_soldier_id, restrain_value))

    redirect("/soldier/restrain")

@route("/soldier/restrain/delete", method="POST")
def soldier_restrain_delete(db):
    soldier_id = request.forms.sid.strip()
    restrain_soldier_id = request.forms.rsid.strip()
    sql = 'DELETE FROM tb_soldier_restrain WHERE soldier_id=%s AND restrain_soldier_id=%s' \
            % (soldier_id, restrain_soldier_id)
    try:
        db.delete(sql)
        return {'result':0, 'data':''}
    except Exception, e:
        return {'result':1, 'data':str(e)}

@route("/soldier/restrain/import", method="POST")
def soldier_restrain_import(db):
    data = request.files.data
    error = ''
    if data and data.file:
        tmp_root = './tmp/'
        if not isdir(tmp_root):
            os.mkdir(tmp_root)
        tmp_filename = os.path.join(tmp_root, current_time('tmpsoldierrestrain_%Y%m%d%H%M.xls'))
        tmp_file = open(tmp_filename, 'w')
        rows = data.file.readlines()
        if not rows:
            error = '数据个数错误[2]'
            return template('error', error=error)
        for row in rows:
            tmp_file.write(row)
        tmp_file.close()
        
        # 导入数据前先备份当前数据库中数据
        export_sqls = SOLDIER_RESTRAIN_EXPORT_SQLS
        try:
            if os.path.exists(os.path.join(tmp_root, SOLDIER_RESTRAIN_BACK_FILE)):
                os.remove(os.path.join(tmp_root, SOLDIER_RESTRAIN_BACK_FILE))
            excel_export(export_sqls, tmp_root, SOLDIER_RESTRAIN_BACK_FILE, db)
        except Exception, e:
            print 'soldier restrain 数据备份错误:%s' %e

        all_sqls = SOLDIER_RESTRAIN_IMPORT_SQLS
        error = excel_import(all_sqls, tmp_filename, db)
        os.remove(tmp_filename)

    else:
        error = '数据格式错误[1]'

    if error:
        # 导入数据错误，进行数据恢复 
        all_sqls = SOLDIER_RESTRAIN_IMPORT_SQLS
        try:
            excel_import(all_sqls, os.path.join(tmp_root, SOLDIER_RESTRAIN_BACK_FILE), db)
            print 'soldier restrain 数据恢复'
        except Exception, e:
            print 'soldier restrain 数据错误:%s' %e
        return template('error', error=error)
    else:
        redirect("/soldier/restrain")

@route("/soldier/restrain/export")
def soldier_restrain_export(db):
    tmp_root = './tmp/'
    filename = current_time('soldierrestrain_%Y%m%d%H%M.xls')
    error = ''

    if not isfile(tmp_root + filename):
        all_sqls = SOLDIER_RESTRAIN_EXPORT_SQLS
        error = excel_export(all_sqls, tmp_root, filename, db)

    if error:
        return template('error', error=error)
    else:
        return static_file(filename, root=tmp_root, download=filename)

@route("/soldier/restrain/recover")
def soldier_restrain_recover(db):
    tmp_root = './tmp/'
    filename = os.path.join(tmp_root, SOLDIER_RESTRAIN_BACK_FILE)
    error = ''
    if not isfile(filename):
        error = '没有soldier restrain 备份文件'
        return template('error', error=error)
    all_sqls = SOLDIER_RESTRAIN_IMPORT_SQLS
    error = excel_import(all_sqls, filename, db)
    if error:
        return template('error', error='数据恢复失败，原因：' + error)
    else:
        redirect("/soldier/restrain")
