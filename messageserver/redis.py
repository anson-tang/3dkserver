#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import py_txredisapi as REDIS

redis = None

def init(conf):
    global redis

    if not redis:
        redis = REDIS.lazyUnixConnectionPool(**conf)


