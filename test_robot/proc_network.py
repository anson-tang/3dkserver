#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 获取网络的使用情况
#

import time

def readnetInfo(dev):
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

    f = open('/proc/net/dev')
    lines = f.readlines()
    f.close()

    res = {'in': 0, 'out': 0}
    for _l in lines:
        if _l.lstrip().startswith(dev):
            _l    = _l.replace(':', ' ')
            items = _l.split()
            res['in']  = long(items[1])
            res['out'] = long(items[len(items)/2 + 1])
            break

    print '{0} Network Info: {1}.'.format( now, res )
    return res


if __name__ == '__main__':
    data = readnetInfo('eth0')
    print 'Current Network Info: {0}.'.format( data )

