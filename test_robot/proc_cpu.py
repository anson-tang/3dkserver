#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 计算cpu的利用率
#      根据两个时刻的数据通过以下方式计算cpu的利用率：100 - (idle2 - idle1)*100/(total2 - total1),
#      其中total = user + system + nice + idle + iowait + irq + softirq
#

import time

def readCpuInfo():
    f = open('/proc/stat')
    lines = f.readlines()
    f.close()

    #print lines
    for _l in lines:
        _l       = _l.lstrip()
        counters = _l.split()
        if len(counters) < 5:
            continue
        if counters[0].startswith('cpu'):
            break

    total = 0
    for _i in xrange(1, len(counters)):
        total = total + long(counters[_i])

    idle = long(counters[4])
    
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    print '{0} total: {1}, idle: {2}.'.format( now, total, idle )
    return {'total': total, 'idle': idle}

def calCpuUsage(counters1, counters2):
    idle  = counters2['idle'] - counters1['idle']
    total = counters2['total'] - counters1['total']

    return 100 - (idle * 100 / total)

if __name__ == '__main__':
    counters1 = readCpuInfo()
    time.sleep(1)
    counters2 = readCpuInfo()

    print 'Current CPU Usage: {0}.'.format( calCpuUsage(counters1, counters2) )

