#-*-coding: utf-8-*-

'''
@version: 0.2
@author: U{Don.Li<mailto: donne.cn@gmail.com>}
@license: Copyright(c) 2012 Don.Li

@summary:
'''

import sys, os

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(current_path + '/../lib'))

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')
