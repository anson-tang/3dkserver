#-*-coding: utf-8 -*-

'''
@version: 0.1.0
@author: U{Don.Li<mailto: donne.cn@gmail.com>}
@license: Copyright(c) 2011 CEC

@summary:
'''

import sys, os
from twisted.python.log import theLogPublisher, err

def loglevel(level=0):
    if isinstance(level, str):
        _l = level.lower()
        if _l.startswith('d'):
            return 1
        elif _l.startswith('i'):
            return 2
        elif _l.startswith('w'):
            return 3
        elif _l.startswith('e'):
            return 4
        elif _l.startswith('c'):
            return 5
        else:
            return 0
    elif isinstance(level, int):
        return level
    else:
        return 0

log_level = 3

def init(threshold):
    global log_level

    try:
        log_level = loglevel(threshold)
    except:
        print '[ W ]:', 'Please set "log_threshold=?." in setting_env.py.'
        
class log:
    @staticmethod
    def _msg(*args, **kwargs):
        kwargs['system'] = '-'
        theLogPublisher.msg(*args, **kwargs)

    @staticmethod
    def debug(*args):
        if log_level <= 1:
            log._msg("\033[37m[ D ]", '[ {0}:{1}({2}) ]'.format( os.path.basename(sys._getframe().f_back.f_code.co_filename), sys._getframe().f_back.f_code.co_name, sys._getframe().f_back.f_lineno ),  ' '.join((str(a) for a in args)), "\033[0m")
        #log._msg('[ D ]', *args, level=1)

    @staticmethod
    def info(*args):
        if log_level <= 2:
            log._msg("\033[32m[ I ]", '[ {0}:{1}({2}) ]'.format( os.path.basename(sys._getframe().f_back.f_code.co_filename), sys._getframe().f_back.f_code.co_name, sys._getframe().f_back.f_lineno ), ' '.join((str(a) for a in args)), "\033[0m")

    @staticmethod
    def warn(*args):
        if log_level <= 3:
            log._msg("\033[33m[ W ]", '[ {0}:{1}({2}) ]'.format( os.path.basename(sys._getframe().f_back.f_code.co_filename), sys._getframe().f_back.f_code.co_name, sys._getframe().f_back.f_lineno ), ' '.join((str(a) for a in args)), "\033[0m")

    @staticmethod
    def error(*args):
        if log_level <= 4:
            log._msg("\033[31m[ E ]", '[ {0}:{1}({2}) ]'.format( os.path.basename(sys._getframe().f_back.f_code.co_filename), sys._getframe().f_back.f_code.co_name, sys._getframe().f_back.f_lineno ), ' '.join((str(a) for a in args)), "\033[0m")

    @staticmethod
    def exception(*args):
        import traceback
        if args:
            log._msg("\033[31m", ' '.join(str(a) for a in args), "\033[0m")
        log._msg("\033[31m", traceback.format_exc(), "\033[0m")
