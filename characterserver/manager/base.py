#!/usr/bin/env python
#-*-coding: utf-8-*-

from attribute import Attribute
from twisted.internet.defer import inlineCallbacks, returnValue
from log import log
from constant import *
from datetime       import datetime

@inlineCallbacks
def new(self, need_load=True, **dict_data):#Return { fn: value }
    if need_load:
        yield self.load(need_value=False)

    _attr = Attribute(self._table)
    _attrib_id = yield _attr.new(**dict_data)
    '''
    try:
        _attrib_id = yield _attr.new(**dict_data)
    except Exception, e:
        raise AttribManagerException("[ %s ]new failed. table:%s, data: %s, error:%s." % ( self.__class__, self._table, dict_data, e))
    '''

    if self._multirow:
        if not isinstance(self.dict_attribs, dict):
            log.warn('[ %s.new ]property dict_attribs is not dict. %s' % ( self.__class__, self.dict_attribs ))
            self.dict_attribs = {}
        self.dict_attribs[_attrib_id] = _attr
    else:
        self.dict_attribs = _attr

    #returnValue( _attr.value )
    returnValue( _attr.new_value() )

@inlineCallbacks
def update(self, data):
    if not data:
        returnValue(None)

    yield self.load(need_value=False)

    try:
        if not self._multirow:
            dict_values = data
            _attr = dict_values
            for k, v in dict_values.iteritems():
                if k in self._time_fields and v:
                    v = datetime.fromtimestamp( int(v) )
                setattr(self.dict_attribs, k, v)
            _attr.update()
        else:
            for primary_key, where, dict_values in data:
                if primary_key:
                    _attr = self.dict_attribs.get( primary_key, None )
                    if _attr:
                        for k, v in dict_values.iteritems():
                            if k in self._time_fields and v:
                                v = datetime.fromtimestamp( int(v) )
                            setattr(_attr, k, v)
                        _attr.update()
                    else:
                        log.warn('[ %s.update ]can not found the attribute, id:%s, data:%s' % (self.__class__, primary_key, dict_values))
                elif where:
                    _found = False

                    for _attr in self.dict_attribs.itervalues():
                        eq = 0

                        for where_k, where_v in where.iteritems():
                            _v = getattr(_attr, where_k, None)
                            if _v == where_v: eq += 1

                        if eq >= len(where):
                            _found = True

                            for k, v in dict_values.iteritems():
                                if k in self._time_fields and v:
                                    v = datetime.fromtimestamp( int(v) )
                                setattr(_attr, k, v)

                    if not _found:
                        log.warn('[ %s.update ]can not found the attribute, where:%s, data:%s' % (self.__class__, where, dict_values))
    except:
        log.exception("[ update ]data: {0}.".format(data))

@inlineCallbacks
def delete(self, primary_key=None, where=None):
    '''
    @where : when primary_key=None, where format like: {'cid':1} 
    '''
    yield self.load(need_value=False)

    if not self._multirow:
        log.warn('[ %s ]Deleted. %s.' % (self.__class__, self.dict_attribs.value))
        self.dict_attribs.delete()
    else:
        if primary_key:
            _attr = self.dict_attribs.pop( primary_key, None )
            if _attr:
                log.debug('[ %s.delete ]deleted, id:%s, data:%s' % ( self.__class__, primary_key, _attr.value ))
                _attr.delete()
                _attr.syncdb()
        elif where:
            _found = False
            for _key, _attr in self.dict_attribs.items():
                eq = 0

                for where_k, where_v in where.iteritems():
                    _v = getattr(_attr, where_k, None)
                    if _v == where_v: eq += 1

                if eq >= len(where):
                    log.debug('[ %s.delete ]deleted, id:%s, where:%s, data:%s' % ( self.__class__, _key, where, _attr.value ))
                    del self.dict_attribs[_key]
                    _attr.delete()
                    _attr.syncdb()
    #log.debug('[ MetaAttrMgr::delete ] end. primary_key {0}, where {1}'.format( primary_key, where ))
    
@inlineCallbacks
def load(self, force=False, where=None, need_value=True):
    ''' Warning! Do not use force-load in multi-line-mode!!! '''
    if not force and self.dict_attribs:
        #returnValue( self.value )
        if need_value:
            returnValue( self.new_value() )
        else:
            returnValue( [] )

    if not where:
        if hasattr(self, 'where'):
            where = self.where
        else:
            raise AttribManagerException("[ %s ]load failed. you can set where property at first." % self.__class__ )

    if self._table not in TABLEs_NO_DELETED:
        where['deleted'] = 0

    try:
        res = yield Attribute.load(self._table, self._fields, where )
    except Exception, e:
        raise AttribManagerException("[ {0} ]load failed. table: {1}, where: {2}, error: {3}.".format( self.__class__, self._table, where, e))

    if self._multirow:
        self.dict_attribs = res
    else:
        if len(res) == 1:
            self.dict_attribs = res.values()[0]
        else:
            #raise AttribManagerException("[ %s ]no data. res:%s, table:%s, where: %s." % ( self.__class__, res, self._table, where))
            log.error("[ {0} ]no data. res:{1}, table:{2}, where:{3}.".format( self.__class__, res, self._table, where ))

    #returnValue( self.value )
    if need_value:
        returnValue( self.new_value() )
    else:
        returnValue( [] )

def syncdb(self):
    if self.dict_attribs:
        if self._multirow and isinstance(self.dict_attribs, dict):
            for attrib in self.dict_attribs.itervalues():
                attrib.syncdb()
        elif isinstance(self.dict_attribs, Attribute):
            self.dict_attribs.syncdb()
        else:
            raise AttribManagerException("[ %s ]unknown dict_attribs type: %s." % (self.__class__, type(self.dict_attribs)))

def isMultiRow(self):
    return self._multirow

def new_value(self):
    values = {}

    if self._multirow:
        if self.dict_attribs:
            for k, attrib in self.dict_attribs.iteritems():
                values[k] = [attrib.value[field] for field in self._fields]
            return values
        else:
            return {}
    else:
        if self.dict_attribs:
            return [self.dict_attribs.value[field] for field in self._fields]
        else:
            return []

@property
def value(self):
    if self._multirow:
        if self.dict_attribs:
            return {k:attrib.value for k, attrib in self.dict_attribs.iteritems()}
        else:
            return {}
    else:
        if self.dict_attribs:
            return self.dict_attribs.value

attrib_properties = {
                     'dict_attribs' : None,
                     'new'          : new,
                     'load'         : load,
                     'delete'       : delete,
                     'syncdb'       : syncdb,
                     'value'        : value,
                     'isMultiRow' : isMultiRow,
                     'update'       : update,
                     'new_value'    : new_value,
                     }

class AttribManagerException(Exception):pass

class MetaAttrManager(type):
    def __new__(cls, name, bases, attribs):
        for _name, _property in attrib_properties.iteritems():
            if _name not in attribs:
                attribs[_name] = _property

        if not attribs.has_key('_fields'):
            raise AttribManagerException("_fields property must be set.")
        if not attribs.has_key('_table'):
            raise AttribManagerException("_table property must be set.")
        if not attribs.has_key('_multirow'):
            #log.warn('[ %s ]_multirow have not been set. default to True, __dict__:%s.' % (name, attribs))
            attribs['_multirow'] = True

        return type.__new__(cls, name, bases, attribs)

    def __init__(cls, name, bases, attribs):
        super(MetaAttrManager, cls).__init__(name, bases, attribs)


