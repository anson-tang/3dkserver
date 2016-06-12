#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1

import os

for sql in os.listdir("."):
    if ".sql" in sql:
        cmd = "mysql -uroot -pdb1234 3dk_userdb < {0}".format(sql)
        try:
            os.system(cmd)
        except e:
            print e
