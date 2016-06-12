#!/usr/bin/env python
#-*-coding: utf-8-*-
import sys

import time
import Queue

from twisted.internet   import reactor, defer
from datetime           import datetime
from protocol_manager   import cs_call
from log                import log
from errorno            import *
from constant           import *
from utils              import datetime2string
from table_fields       import TABLE_FIELDS

def sync_gs_dirty_attributes(queue, loop=True):
    _len = queue.qsize()
    if _len > 0:
        if loop:
            _times = min(_len, MAX_SYNC_CS_CNT_PER_LOOP) 
        else:
            _times = _len

        i = 0
        dirty_attributes = []
        while i < _times:
            i += 1

            try:
                attr  = queue.get_nowait()
                _data = attr.syncDirtyAttrToCS()
                if _data:
                    dirty_attributes.append( _data )
            except Queue.Empty:
                break
            except Exception as e:
                log.error('Exp3029882 e:', e)

        if dirty_attributes:
            cs_call('cs_sync_user_attribute', (dirty_attributes, ))
        log.info('End sync, total attributes: {0}, left dirty attributes length: {1}.'.format( _times, queue.qsize()))

    if loop:
        reactor.callLater(SYNC_CS_INTERVAL, sync_gs_dirty_attributes, queue)
    else:
        log.warn('End sync, dirty attributes length {0}, loop:{1}.'.format(queue.qsize(), loop))

try:
    g_DirtyGSAtrributeQueue
except NameError:
    g_DirtyGSAtrributeQueue = Queue.Queue()
    reactor.callLater(SYNC_DB_INTERVAL, sync_gs_dirty_attributes, g_DirtyGSAtrributeQueue)
    reactor.addSystemEventTrigger('before', 'shutdown', sync_gs_dirty_attributes, g_DirtyGSAtrributeQueue, False)

class GSAttribute(object):
    def __init__(self, cid, name, row_id=0):
        self.__cid       = cid
        self.__name      = name
        self.__row_id    = row_id #Primary key of row
        self.__fields    = TABLE_FIELDS[name][0]
        self.__field_set = set( TABLE_FIELDS[name][0] )

        self.__time_fields = TABLE_FIELDS[name][1]

        self.__dirty        = False
        self.__dirty_fields = set()

    @property
    def value(self):
        dv = {'id': self.__row_id}
        for k, v in self.__dict__.iteritems():
            if not k.startswith('_'):
                if isinstance(v, datetime):
                    v = int(time.mktime(v.timetuple()))
                #    v = v.strftime("%Y-%m-%d %H:%M:%S")
                dv[k] = v
        return dv

    @property
    def cid(self):
        return self.__cid    

    @property
    def attrib_id(self):
        return self.__row_id
    
    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

    def __setitem__(self, attr_name, attr_value):
        self.__dict__[attr_name] = attr_value
        if not attr_name.startswith('_'):
            self.dirty(attr_name)

    def __setattr__(self, attr_name, attr_value):
        self.__dict__[attr_name] = attr_value
        if not attr_name.startswith('_'):
            self.dirty(attr_name)

    @staticmethod
    @defer.inlineCallbacks
    def load(cid, table):
        attribs = {}
        try:
            res_err, table_data = yield cs_call('cs_load_table_data', (cid, table))
            #log.info('For Test. res_err: {0}, length: {1}.'.format( res_err, len(table_data) ))
            if res_err:
                log.error('load table({0}) data error. table_data: {1}.'.format( table, table_data ))
                defer.returnValue( attribs )

            _table_fields = TABLE_FIELDS[table][0]
            for attrib_id, row in table_data.iteritems():
                attr = GSAttribute(cid, table, attrib_id)
                attr.updateGSAttribute( False, **dict(zip(_table_fields, row)) )
                if attr.attrib_id not in attribs:
                    attribs[attr.attrib_id] = attr
                else:
                    log.error('Exception table data. attrib_id: {0}.'.format( attr.attrib_id ))

            defer.returnValue( attribs )
        except Exception as e:
            log.error( 'Exception raise. e: {0}.'.format( e ))
            raise e
            #defer.returnValue( attribs )

    @defer.inlineCallbacks
    def new(self, **kwargs):
        try:
            res_err, create_data = yield cs_call('cs_new_attrib', (self.__cid, self.__name, True, kwargs))
            if res_err:
                log.error('create table({0}) data error. create_data: {1}.'.format( self.__name, create_data ))
                defer.returnValue( res_err )

            self.updateGSAttribute(False, **dict(zip(self.__fields, create_data)) )
            defer.returnValue( res_err )
        except Exception as e:
            log.error( 'Exception raise. e: {0}.'.format( e ))
            defer.returnValue( UNKNOWN_ERROR )

    def updateGSAttribute(self, _dirty=True, **kwargs):
        if 'id' in kwargs:
            self.__row_id  = kwargs.pop('id')
        for _field in self.__time_fields:
            _stamp = kwargs.get(_field, 0)
            _stamp = _stamp if _stamp else 0
            kwargs[_field] = datetime.fromtimestamp( int(_stamp) )
        self.__dict__.update(kwargs)

        if _dirty:
            for k in kwargs.keys():
                if not k.startswith('_'):
                    self.dirty(k)

    def dirty(self, k=None):
        if not self.__dirty:
            g_DirtyGSAtrributeQueue.put(self)
            self.__dirty = True

        if not k:
            return

        if k in self.__field_set:
            if k not in self.__dirty_fields:
                self.__dirty_fields.add(k)
        else:
            pass #log.debug('[ GSAttribute::dirty ] Tbl {0}, {1} not in field-set {2}'.format( self.__name, k, self.__field_set ))

    def clean_dirty(self):
        self.__dirty = False
        self.__dirty_fields.clear()

    def delete(self):
        #log.debug('delete attribute, set delete=1. cid: {0}, attrib_id: {1}.'.format( self.__cid, self.__row_id ))
        if hasattr(self, 'deleted') and hasattr(self, 'del_time'):
            self.deleted  = 1
            #self.del_time = datetime2string()
            self.del_time = datetime.now()
        else:
            raise Exception( "GsAttribute( %s ) have no attribute deleted or del_time. dict:%s." % (self.__name, list(self.__field_set) ) )

    def syncToCS(self):
        if not self.__dirty:
            #log.info('For Test. no data need sync to cs.')
            return
        #log.info('For Test. GSAttribute::syncToCS, self.__dirty_fields:', self.__dirty_fields)
        if hasattr(self, 'update_time'):
            self.update_time = datetime.now()

        dirty_data = {}
        for fn in self.__dirty_fields:
            dirty_data[fn] = self.__dict__[fn]

        cs_call('cs_sync_user_attribute', ([(self.__cid, self.__name, self.__row_id, dirty_data)], ))
        self.clean_dirty()

    def syncDirtyAttrToCS(self):
        if not self.__dirty:
            return None

        if hasattr(self, 'update_time'):
            self.update_time = datetime.now()

        dirty_data = {}
        for fn in self.__dirty_fields:
            dirty_data[fn] = self.__dict__[fn]

        self.clean_dirty()

        if dirty_data:
            return ( (self.__cid, self.__name, self.__row_id, dirty_data) )
        else:
            return None


