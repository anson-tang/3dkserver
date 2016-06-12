#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle  import route, template, request
from json import dumps, loads
import os

@route('/sync_daily_server_view')
def sync_daily_server_view():
    return template('sync_daily_server',  tpl_data={})

@route('/sync_daily_server', method="POST")
def sync_daily_server():
    #os.system('../sync_svn_update')
    out1 = os.popen('netstat -tnpl | grep "python" ').read()
    return {'out1':out1}

