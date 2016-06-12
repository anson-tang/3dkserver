#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, returnValue
from protocol_manager import gs_call
from log import log
from errorno import *
from constant import *

from manager.character        import Character
from manager.fellow           import CSFellowMgr
#from manager.bag              import BagNormal
from manager.csbag_fellowsoul import CSBagFellowsoulMgr
from manager.csbag_item       import CSBagItemMgr
from manager.csbag_treasure   import CSBagTreasureMgr
from manager.csbag_equip      import CSBagEquipMgr
from manager.csbag_equipshard import CSBagEquipshardMgr
from manager.csbag_jade       import CSBagJadeMgr
from manager.csclimbing_tower import CSClimbingMgr
from manager.csscene          import CSSceneMgr
from manager.cselitescene     import CSEliteSceneMgr
from manager.csactivescene    import CSActiveSceneMgr
from manager.csatlaslist      import CSAtlaslistMgr
from manager.csgoodwill       import CSGoodwillMgr


from manager.csbag_treasureshard   import CSBagTreasureShardMgr

MANAGERS = {    
                'fellow': CSFellowMgr,
        'bag_fellowsoul': CSBagFellowsoulMgr,
              'bag_item': CSBagItemMgr,
          'bag_treasure': CSBagTreasureMgr,
     'bag_treasureshard': CSBagTreasureShardMgr,
             'bag_equip': CSBagEquipMgr,
        'bag_equipshard': CSBagEquipshardMgr,
              'bag_jade': CSBagJadeMgr,
        'climbing_tower': CSClimbingMgr,
                 'scene': CSSceneMgr,
            'elitescene': CSEliteSceneMgr,
           'activescene': CSActiveSceneMgr,
             'atlaslist': CSAtlaslistMgr,
              'goodwill': CSGoodwillMgr,
        }


class CSUser(object):
    def __init__(self, cid):
        self.cid = cid
        self._managers = {}

    def register(self, table, manager):
        #log.debug('register. table: {0}, manager: {1}.'.format( table, manager ))
        self._managers[table] = manager

    @property
    def getAllManager(self):
        return self._managers

    def getManager(self, table):
        return self._managers.get( table, None )

    def registerManager(self, table):
        ''' register by table
        '''
        _manager = MANAGERS.get(table, None)
        #log.debug('registerManager. table: {0}, _manager: {1}.'.format( table, _manager ))
        if _manager:
            _manager(self, self.cid)

        return _manager

    def syncAllManagers(self):
        for m in self._managers.itervalues():
            m.syncdb()

    def create_aux_data(self, new_cid):#Retrun: errno, fellow, bag
        fellow= CSFellowMgr(new_cid)
        fellow.register(self)

        #bag_normal = BagNormal(new_cid)
        #bag_normal.register(self)

        #return 0, fellow, bag_normal
        return 0, fellow

    @defer.inlineCallbacks
    def load_aux_data(self):#Return: errno, fellow_data, bag_normal_data
        res_err = (UNKNOWN_ERROR, {}, {})

        fellow= CSFellowMgr(self.cid)
        fellow.register(self)
        fellow_data = {}
        bag_data = {}
        try:
            fellow_data = yield fellow.load()
        except Exception as e:
            log.debug('Exp raise in Fellow::load(). e:', e)
            defer.returnValue(res_err)

        #bag_normal = BagNormal(self.cid)
        #bag_normal.register(self)
        #try:
        #    bag_normal_data = yield bag_normal.load()
        #except Exception as e:
        #    log.debug('Exp raise in BagNormal::load(). e:', e)
        #    defer.returnValue(res_err)
        #log.debug('Load bag:', bag_normal_data, '/////////////////////////////////////////////////')
        #defer.returnValue( ( 0, fellow_data, bag_normal_data ) )
        #defer.returnValue( ( 0, fellow_data ) )
        defer.returnValue( ( 0, fellow.new_value() ) )


class CSUserMgr(object):
    def __init__(self):
        self.__dict = {}

    def getUser(self, cid):
        #log.debug('Print __dict:', self.__dict)
        if self.__dict.has_key(cid):
            return self.__dict[cid]
        else:
            return None

    def register(self, cid, table, manager):
        _user = self.__dict.get(cid, None)
        if not _user:
            _user = CSUser(cid)
            self.__dict[cid] = _user

        _user.register(table, manager)
        return _user

    def unregister(self, cid):
        if cid in self.__dict:
            log.debug('User logout sucess. cid:', cid)
            del self.__dict[cid]
        else:
            log.warn('Unknown user. cid:', cid)

g_UserMgr = CSUserMgr()
