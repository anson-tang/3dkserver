#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle  import route, template, request
from json import dumps, loads
import os

@route('/reboot_server_view')
def reboot_server_view():
    return template('reboot_server',  tpl_data={})

@route('/reboot_server', method="POST")
def reboot_server():
    #os.system('make')
    #os.system('../stop')
    #os.system('../start')
    os.system('../reboot_daily')
    out1 = os.popen('netstat -tnpl | grep "python" ').read()
    return {'out1':out1}

