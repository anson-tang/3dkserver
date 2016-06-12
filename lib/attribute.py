#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2012 Don.Li
# Summary: 

from datetime import datetime
from _mysql   import escape
import time
import Queue
from db import db
from log import log
from twisted.internet import reactor, defer
from constant import *
from table_fields   import TABLE_FIELDS


TABLE_PREFIX = 'tb_'

def sync_dirty_attributes(queue, loop=True):
    _l = queue.qsize()
    if _l > 0:
        if loop:
            _times = min(_l, MAX_SYNC_CNT_PER_LOOP) 
        else:
            _times = _l

        i = 0
        while i < _times:
            i += 1

            try:
                attr = queue.get_nowait()
                attr.syncdb()
            except Queue.Empty:
                break
            except:
                pass

        log.info('End sync character to db, total: {0}, dirty attributes length: {1}'.format( _times, queue.qsize() ))

    if loop:
        reactor.callLater(SYNC_DB_INTERVAL, sync_dirty_attributes, queue)
    else:
        log.debug('End sync db, dirty attributes length {0}, loop:{1}'.format(
            queue.qsize(), loop))

try:
    DIRTY_ATTRIBUTES
except NameError:
    DIRTY_ATTRIBUTES = Queue.Queue()
    reactor.callLater(SYNC_DB_INTERVAL, sync_dirty_attributes, DIRTY_ATTRIBUTES)
    reactor.addSystemEventTrigger('before', 'shutdown', sync_dirty_attributes, DIRTY_ATTRIBUTES, False)

class AttributeError(Exception):pass

class Attribute(object): #Present one row in db
    def __init__(self, name):
        self.__name  = name
        self.__uid   = 0
        self.__new   = False
        self.__del   = False
        self.__dirty = False

        self.__dirty_fields = []
        
        self.__fields = [ v for v in TABLE_FIELDS[self.__name][0] if v != 'id']
        self.__time_fields = TABLE_FIELDS[self.__name][1]
 
    @property
    def table(self):
        return TABLE_PREFIX + self.__name

    @property
    def value(self):
        dv = {'id': self.__uid}
        for k, v in self.__dict__.iteritems():
            if not k.startswith('_'):
                if isinstance(v, datetime):
                    v = int(time.mktime(v.timetuple()))
                dv[k] = v

        return dv

    def new_value(self):
        new_value = [self.__uid]
        for field in self.__fields:
            v = self.__dict__[field]
            if isinstance(v, datetime):
                v = int(time.mktime(v.timetuple()))
            new_value.append(v)
        return new_value

    def __str__(self):
        return str(self.value)
    __repr__ = __str__

    @property
    def attrib_id(self):
        return self.__uid

    @defer.inlineCallbacks
    def new(self, **kwargs):

        _dirty_fields = []
        _values       = []

        for k, v in kwargs.iteritems():
            _dirty_fields.append(k)
            if k in self.__time_fields and v:
                v = datetime.fromtimestamp( v )
                kwargs[k] = v
            _values.append(v)
        self.__dict__.update(kwargs)
        _sql = 'INSERT INTO %s (' % self.table  + ','.join(_dirty_fields) + ') VALUES (' \
                            + ','.join(['%s'] * len(_values)) + ')'

        res = yield db.insert(_sql, _values)
        if self.table == 'tb_character':
            if res > 1000000:
                db.execute('DELETE FROM {0} WHERE id={1};'.format(self.table, res))
                log.error('insert error. res:{0}, _values:{1}.'.format( res, _values ))
                raise AttributeError('Attribute: insert new character id error')

            new_res = kwargs.get('sid', 1001)*1000000 + res
            db.execute('UPDATE {0} SET id={1} WHERE id={2};'.format(self.table, new_res, res))
            self.__uid = new_res
            log.error('For Test. table:{0}, res:{1}, new_res:{2}.'.format( self.table, res, new_res ))
        else:
            self.__uid = res
        defer.returnValue(self.__uid)

    @staticmethod
    @defer.inlineCallbacks
    def load(name, fields, where):
        if 'id' not in fields:
            raise AttributeError('[ Attribute:{0} ]attribute id is must.'.format(name))
        else:
            _sql = 'SELECT {0} FROM {1} WHERE {2};'.format(','.join(fields),
                            TABLE_PREFIX + name, '1 AND' + ' AND '.join([' %s=%s' % (k, "'%s'" % v if isinstance(v, (str, unicode)) else v ) for k, v in where.iteritems()]))
            _dataset = yield db.query(_sql)

            attribs  = {}
            if _dataset:
                for row in _dataset:
                    _attr = Attribute(name)
                    _attr.update(False, **dict(zip(fields, row)))
                    attribs[_attr.attrib_id] = _attr

            defer.returnValue(attribs)

    def update(self, _dirty=False, **kwargs):
        if 'id' in kwargs:
            self.__uid  = kwargs.pop('id')
        self.__dict__.update(kwargs)

        if _dirty:
            for k in kwargs.keys():
                if not k.startswith('_'):
                    self.dirty(k)

    def delete(self):
        if self.__uid > 0:
            self.__del = True
            self.dirty()

    def __setattr__(self, attr_name, attr_value):
        self.__dict__[attr_name] = attr_value
        if not attr_name.startswith('_'):
            self.dirty(attr_name)

    def __gen_update_value(self, fields):
        _sql = 'UPDATE %s SET {0} WHERE id=%s' % (self.table, self.__uid)
        values = []
        fields_str = ''

        field_num = 1
        for field in fields:
            values.append(getattr(self, field))
            if field_num < len(fields):
                fields_str += '{0}=%s,'.format(field)
            else:
                fields_str += '{0}=%s'.format(field)
            field_num += 1

        _sql = _sql.format(fields_str)

        return _sql, values

    def syncdb(self):
        if self.__dirty:
            _dirty_fields = self.__dirty_fields[:]

            if len(_dirty_fields) == 0 and False == self.__del:
                log.info('no dirty_fields! table name:{0}, attrib_id:{1}.'.format( self.table, self.__uid ))
                return

            _sql = ''

            try:
                if self.__del:
                    db.execute('DELETE FROM {0} WHERE id={1};'.format(self.table, self.__uid))
                else:
                    _sql, _v = self.__gen_update_value(_dirty_fields)
                    if _v:
                        db.execute(_sql, _v)
                    else:
                        log.warn('Update error. table: {0}, cid: {1}, sql: {2}, dirty: {3}.'.format(self.table, self.__uid, _sql, self.__dirty_fields))
            except:
                log.exception('[ SQLERROR ]table:{0}, id:{1}, dirty:{2}, new:{3}, dirty_fields:{4}, sql:{5}'.format(
                    self.table, self.__uid, self.__dirty, self.__new, self.__dirty_fields, _sql))
            else:
                self.clean()

    def dirty(self, k=None):
        if not self.__dirty:
            DIRTY_ATTRIBUTES.put(self)
            self.__dirty = True

        if k and k not in self.__dirty_fields:
            self.__dirty_fields.append(k)

    def clean(self):
        self.__dirty = False
        del self.__dirty_fields[:]
