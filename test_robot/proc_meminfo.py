#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 计算内存的利用率
#       计算内存的利用率需要读取的是/proc/meminfo文件
#       内存的使用总量为used = total - free - buffers - cached
#


import time


def readMemInfo():
    res = {'total':0, 'free':0, 'buffers':0, 'cached':0}

    f = open('/proc/meminfo')
    lines = f.readlines()
    f.close()

    #print 'meminfo: ', lines
    i = 0
    for _l in lines:
        if i == 4:
            break
        _l = _l.lstrip()
        memItem = _l.lower().split()

        if memItem[0] == 'memtotal:':
            res['total'] = long(memItem[1])
            i = i + 1
            continue
        elif memItem[0] == 'memfree:':
            res['free'] = long(memItem[1])
            i = i + 1
            continue
        elif memItem[0] == 'buffers:':
            res['buffers'] = long(memItem[1])
            i = i + 1
            continue
        elif memItem[0] == 'cached:':
            res['cached'] = long(memItem[1])
            i = i + 1
            continue

    now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    print '{0} mem info: {1}.'.format( now, res )
    return res

def calMemUsage(counters):
    used  = counters['total'] - counters['free'] - counters['buffers'] - counters['cached']
    total = counters['total']

    return used * 100 / total

if __name__ == '__main__':
    counters = readMemInfo()
    print 'Current Mem Usage: {0}.'.format( calMemUsage(counters) )


