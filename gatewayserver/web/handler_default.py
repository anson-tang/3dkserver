#!/usr/bin/env python
# -*- coding: utf-8 -*-

from systemdata import load_all_config, load_all_keyword, load_all_randname
from constant   import *
from gm_errorno import *
from twisted.internet import defer

import time
import json
import datetime
import decimal

import gemsgpack
import struct

import hashlib

from log import log
from manager.gateuser import g_UserMgr
from protocol_manager import protocol_manager, gs_call
from utils import datetime2time, datetime2string

from ban_word import ban_word_chat, ban_word_name

use_zip        = True
json_sysconfig = None
json_keyword   = {}
json_randname  = None

sysconfig   = load_all_config(FOR_CLIENT_ONLY)
all_keyword = load_all_keyword()
randname    = load_all_randname()

cross_domain_xml = '''<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
    <allow-access-from domain="*" />
</cross-domain-policy>
'''

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime.datetime):
            return datetime2string(o)
        return super(DecimalEncoder, self).default(o)

def load_randname():
    global json_randname

    if json_randname: return
    log.info('randname: {0}.'.format( randname ))
    if use_zip:
        import StringIO, gzip

        out = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=out, mode='w')
        f.write(gemsgpack.dumps( randname ))
        f.close()
        json_randname = out.getvalue()
        out.close()
    else:
        json_randname = json.dumps( randname , cls=DecimalEncoder)

def load_keyword():
    global json_keyword

    if json_keyword: return

    if use_zip:
        import StringIO, gzip

        for k, v in all_keyword.iteritems():
            out = StringIO.StringIO()
            f = gzip.GzipFile(fileobj=out, mode='w')
            f.write(gemsgpack.dumps(v))
            #f.write(gemsgpack.dumps(v, cls=DecimalEncoder))
            f.close()
            json_keyword[k] = out.getvalue()
            out.close()
    else:
        for k, v in all_keyword.iteritems():
            json_keyword[k] = json.dumps(v, cls=DecimalEncoder)

SEP_TABLE = '!&!'
SEP_TABLE_NAME = '!&&'

def load_sys_config():
    global json_sysconfig

    if json_sysconfig: return

    if use_zip:
        import StringIO, gzip

        out = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=out, mode='w')

        for k, table_value in sysconfig.iteritems():
            f.write(struct.pack('!I%ss' % len(k), len(k), k))
            s = gemsgpack.dumps(table_value)
            f.write(struct.pack('!I%ss' % len(s), len(s), s))

        f.close()
        json_sysconfig = out.getvalue()
        out.close()
    else:
        json_sysconfig = json.dumps(sysconfig, cls=DecimalEncoder)

def reload_sysconfig(request):
    try:
        reload_config()
        load_sys_config()
        load_randname()
        return {'result':0, 'error':''}
    except Exception, e:
        sys.stderr.write(str(e) + "\n")
        return {'result':1, 'error':str(e)}

def sys_keyword(request):
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')

    args = request.args
    lang = '0'
    if args.has_key('lang'):
        lang = args['lang'][0]


    if args.has_key('unzip'):
        unzip = args['unzip'][0]

        if unzip != '0':
            keyword = all_keyword.get(lang, {})
            return json.dumps(keyword, cls=DecimalEncoder)

    return json_keyword.get(lang, {})

def sys_config(request):
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')

    args = request.args
    if args.has_key('unzip'):
        unzip = args['unzip'][0]

        if unzip != '0':
            return json.dumps(sysconfig, cls=DecimalEncoder)

    return json_sysconfig

def sys_randname(request):
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')

    args = request.args
    if args.has_key('unzip'):
        unzip = args['unzip'][0]

        if unzip != '0':
            return json.dumps(randname, cls=DecimalEncoder)

    return json_randname

def ban_word(request):
    request.setHeader('Content-Type', 'application/json;charset=UTF-8')

    args = request.args
    if args.has_key('t'):
        t = args['t'][0]

        if t == 'chat':
            return ban_word_chat()
        elif t == 'name':
            return ban_word_name()
        else:
            return ""

load_sys_config()
load_keyword()
load_randname()
