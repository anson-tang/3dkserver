#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from bottle import route, static_file
from utils  import pprint
import time

@route("/static/<filepath:path>")
def static_serve(filepath):
    return static_file(filepath, root='./static/')

@route("/protocol/<filepath:path>")
def protocol_serve(filepath):
    return static_file(filepath, root='./phtml/')
