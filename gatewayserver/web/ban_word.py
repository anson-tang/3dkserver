#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path   import getmtime, abspath, dirname
from utils     import print_e
from gemsgpack import dumps

import StringIO, gzip

_path              = abspath(dirname(__file__) + '/banword')
banword_chat_file  = _path + '/ban_word_chat'
banword_name_file  = _path + '/ban_word_name'

last_modified_chat = getmtime( banword_chat_file )
last_modified_name = getmtime( banword_name_file )

def __read_file( path ):
    result = []

    try:
        result = [ line.rstrip('\r\n') for line in file( path ).readlines() ]
    except:
        print_e()

    #print '[ __read_file ]result:', result

    out = StringIO.StringIO()
    f = gzip.GzipFile( fileobj = out, mode = 'w' )
    f.write( dumps( result ) )
    f.close()

    return out.getvalue()

__BAN_WORD_CHAT = __read_file( banword_chat_file )
__BAN_WORD_NAME = __read_file( banword_name_file )

def ban_word_chat():
    global last_modified_chat, __BAN_WORD_CHAT

    _last_modified_chat = getmtime( banword_chat_file )
    if _last_modified_chat != last_modified_chat:
        __BAN_WORD_CHAT = __read_file( banword_chat_file )
        last_modified_chat = _last_modified_chat

    return __BAN_WORD_CHAT

def ban_word_name():
    global last_modified_name, __BAN_WORD_NAME

    _last_modified_name = getmtime( banword_name_file )
    if _last_modified_name != last_modified_name:
        __BAN_WORD_NAME = __read_file( banword_name_file )
        last_modified_name = _last_modified_name

    return __BAN_WORD_NAME
