#-*-coding:utf-8-*-
from os.path import isfile, isdir
from utils   import pprint
import os
import sys
import xlrd, xlwt

update_sql_sysconfig = "UPDATE tb_config_version SET SysconfigVer=SysconfigVer+1 WHERE ID=1;"
update_sql_keyword   = "UPDATE tb_config_version SET KeywordVer=KeywordVer+1 WHERE ID=1;"

def excel_import(all_sqls, tmp_filename, db):
    error    = ''
    miss_all = False

    # 更新多语言的标志位
    flag_keyword   = False
    # 更新sysconfig的标志位
    flag_sysconfig = False

    wb = xlrd.open_workbook(tmp_filename)
    for sh in wb.sheets():
        if sh.name not in all_sqls.keys():
            miss_all = True
            continue

        if sh.name == 'Message':
            flag_keyword = True
        else:
            flag_sysconfig = True

        miss_all = False
        table_name = all_sqls[sh.name][1]  # sheet名称，同时为数据表名
		
        contents = []
        for i in range(1, sh.nrows):
            #contents.append(sh.row_values(i))
            row_data = sh.row_values(i)  # table_name 数据表的一条数据
            if row_data[0]:
                contents.append(row_data)
            elif row_data[0] == 0:
                contents.append(row_data)
        try:
            # table_name数据表
            db.execute('DELETE FROM %s;' % table_name)
            sql = all_sqls[sh.name][0]
            #pprint(table_name, sh.name, sql, contents)
            if contents:
                db.executemany(sql, contents)
        except Exception, e:
            error = 'import %s error: %s, sql:%s, contents:%s' %(table_name, e, sql, contents)

    if miss_all:
        error = 'sheet名称错误, sheet:%s, all:%s' % ([sh.name for sh in wb.sheets()], all_sqls.keys())
    else:
        if flag_keyword: # 更新的多语言配置
            db.execute( update_sql_keyword )

        if flag_sysconfig: # 更新的sysconfig配置
            db.execute( update_sql_sysconfig )

    return error
     
def excel_export(all_sqls, tmp_root, filename, db):
    error = ''
    workbook = xlwt.Workbook()  # 打开excel文件
    # 生成多个sheet
    for sheet_contents in all_sqls.itervalues():
        sql        = sheet_contents[0]
        db.execute(sql)
        all_result = db.fetchall()
        title      = sheet_contents[1]
        sheet_name = sheet_contents[2]

        try:
            sh = workbook.add_sheet(sheet_name)  # 新建一个名为sheet_name的sheet
            rows = []

            rows.append(title)  # 添加第一行(标题)

            for data in all_result:  # 迭代查询结果，填充list, -------未知db.select(sql)返回的数据格式-------
                row = []  
                for c in data:
                    try:
                        row.append(str(c).strip())
                    except Exception, e:
                        print 'error ', str(e), c, type(c)
                rows.append(row)

            for i, row in enumerate(rows):  # 迭代rows，将数据写入excel文件
                for j, c in enumerate(row):
                    if type(c).__name__ == 'str':
                        c = c.decode('utf-8')
                    try:
                        sh.write(i, j, c) 
                    except Exception, e:
                        print 'write error ', str(e), i, j, c

        except Exception, e:
            print 'error sheet_name: %s' %sheet_name, str(e)
            error = str(e)

    if not isdir(tmp_root):  # 若目录tmp_root不存在，则创建
        os.mkdir(tmp_root)
    try:
        workbook.save(os.path.join(tmp_root, filename))  # 用文件名filename保存excel文件 
    except Exception, e:
        print 'save error ', str(e)
    return error

