#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import config
from dbhelper import DBHelper

try:
    db
except NameError:
    db = DBHelper(**config.db_conf)
