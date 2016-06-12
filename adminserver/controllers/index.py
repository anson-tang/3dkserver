#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle import route, template
from utils  import pprint

@route('/')
def index():
    return template('base')

@route("/default")
def firstpage():
    '''
    url = "http://{0}:{1}"
    from config import conf

    for section in conf.sections():
        if section.startswith('WEBSERVER'):
            url = url.format(conf.get(section, 'host'), conf.getint(section, 'port'))
            break
    else:
        url = url.format('192.168.8.233', 8082)
    '''

    url = "未知"
    print url

    return template('default', url=url)
