#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 


from log      import log
from time     import time
from errorno  import *
from constant import *

from twisted.internet import defer
from protocol_manager import cs_call


@defer.inlineCallbacks
def gs_load_table_data(cid, table):
    try:
        res_err, table_data = yield cs_call('cs_load_table_data', (cid, table))
        if res_err:
            log.error('Load table data error. cid: {0}, table: {1}.'.format( cid, table ))
            defer.returnValue( None )

        defer.returnValue( table_data )
    except Exception as e:
        log.error( 'Exception raise. e: {0}.'.format( e ))
        defer.returnValue(res_err)

@defer.inlineCallbacks
def gs_create_table_data(*args, **kwargs):
    cid, table = args
    try:
        res_err, create_data = yield cs_call('cs_new_attrib', (cid, table, False, kwargs))
    except Exception as e:
        log.error( 'Exception raise. e: {0}.'.format( e ))
        defer.returnValue(res_err)

    if res_err:
        log.error('Create table data error. cid: {0}, table: {1}.'.format( cid, table ))
        defer.returnValue( None )
    else:
        defer.returnValue( create_data )

#@defer.inlineCallbacks
#def gs_delete_table_data(*args, **kwargs):
#    res_err = [UNKNOWN_ERROR, None]
#
#    cid, table, attrib_id = args
#    try:
#        delete_data = yield cs_call('cs_delete_attrib', (cid, table, attrib_id))
#    except Exception as e:
#        log.error( 'Exception raise. e: {0}.'.format( e ))
#        defer.returnValue(res_err)
#
#    defer.returnValue(delete_data)


