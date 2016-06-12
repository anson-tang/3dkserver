#-*-coding:utf-8-*-

#from twisted.internet import defer
#import time
#from log import log
#from marshal  import loads, dumps     
#
#from errorno import *
#from constant import *
#
#from system import sysconfig
#from redis    import redis
#
#
#class MonsterCfgMgr(object):
#    def __init__(self):
#        #self.dic_monsterid_data = {}#k: MonsterID  v:{'MonsterID': 6L, 'Money': 2222L, 'Soul': 512L, 'attributes': [ {fn:value}, ... ], 'Diff': 2, 'DungeonID': 101102L}
#        self.dic_dungeonid_bonus = {}#k: dungeonid  v: { diff : { Soul:xx, Money:xx }, ... }
#        self.buildData()
#
#    #def getDicMonsterIDData(self):
#    #    return self.dic_monsterid_data
#
#    def getDicDungeonIDBonus(self):
#        return self.dic_dungeonid_bonus
#
#    def buildData(self):
#        log.debug('[ MonsterCfgMgr::buildData ] dungeon cfg ')
#        dataset = sysconfig['monster']
#        #l1-dic: k: dungeon_id, v: l2-dic
#        #l2-dic: k: diff, v: data
#        for dgn_id, diff_dic in dataset.iteritems():
#            dgn_cfg = dataset[int(dgn_id)]
#            self.dic_dungeonid_bonus[ dgn_id ] = dgn_cfg
#            #log.debug('[ MonsterCfgMgr::buildData ] dungeon cfg :', dgn_cfg)
#
#    def buildDataOld(self):
#        dataset = sysconfig['monster']
#        for id, row in dataset.iteritems():
#            dungeon_id = row['DungeonID']
#            Diff = row['Diff']
#            Soul = row['Soul']
#            Money = row['Money']
#
#            bonus = None
#            if dungeon_id in self.dic_dungeonid_bonus:
#                bonus = self.dic_dungeonid_bonus[dungeon_id]
#            else:
#                bonus = {}
#                self.dic_dungeonid_bonus[dungeon_id] = bonus
#
#            bonus[Diff] = { 'Soul':Soul, 'Money':Money }
#
#            monster_id = row['MonsterID']
#            monster = self.dic_monsterid_data.get(monster_id, None)
#            if not monster:
#                monster = {}
#                monster.update( row )
#                self.dic_monsterid_data[monster_id] = monster
#        log.debug('[ MonsterCfgMgr::buildData ] end. dic_monsterid_data:', self.dic_monsterid_data)
#        log.debug('[ MonsterCfgMgr::buildData ] end. dic_dungeonid_bonus:', self.dic_dungeonid_bonus)
#
#g_MonsterCfgMgr = MonsterCfgMgr()
#
#class TownCfgMgr(object):
#    def __init__(self):
#        dic_dungeon, dic_townid__turn_dungeon = sysconfig['scene_dungeon'] #k: town_id v: dic_field ( fields : DungeonID, Turn, Type, RushMax, TownID )
#        self.__dic_dungeon = dic_dungeon
#        self.__dic_townid__dic_turn_dungeon = dic_townid__turn_dungeon
#        self.__dic_townid__list_dungeon = {}
#
#        #log.debug('Print cfg of scene_dungeon:-----------------------')
#        #for row in self.__dic_townid__dic_turn_dungeon.itervalues():
#        #    log.debug('rows_scene_dungeon:', row)
#
#        for town_id, dic_l2 in self.__dic_townid__dic_turn_dungeon.iteritems():
#            l2_dic_turn_dgn = self.__dic_townid__dic_turn_dungeon[town_id]
#            data_list = []
#            MAX_DUNGEON_COUNT_PER_TOWN = 30
#            for i in range(1, MAX_DUNGEON_COUNT_PER_TOWN):
#                if i not in l2_dic_turn_dgn:
#                    break;
#                data = l2_dic_turn_dgn[i]
#                data_list.append( data )
#            self.__dic_townid__list_dungeon[town_id] = data_list
#
#    def getDicTownDungeon(self):
#        return self.__dic_townid__dic_turn_dungeon;
#
#    def getDungeonListInTown(self, town_id):
#        if town_id not in self.__dic_townid__list_dungeon:
#            return None
#
#        return self.__dic_townid__list_dungeon[town_id]
#
#    def getDungeonCfg(self, dungeon_id):
#        if dungeon_id in self.__dic_dungeon:
#            return self.__dic_dungeon[dungeon_id]
#        else:
#            return None
#
#g_TownCfgMgr = TownCfgMgr()
#
#
#class TownAdventureHistory(object):
#    def __init__(self, cid, town_id):
#        self.cid = cid
#        self.town_id = town_id
#        self.brief_history = {} #field: last_scene_star
#        self.brief_history['last_scene_star'] = 0
#        self.__dgn_his_list = [] #list-ele: dungeon_history(dic) #Fields: dungeon_id, dungeon_star, dungeon_today_challenge, dungeon_last_challenge_time
#        self.__dgn_his_dic = {} #k: dungeon_id, v:dungeon_history(dic) # It's redundant.
#        # 未掉落时, drop_id掉落概率增加次数 format: {drop_id: count, ...}
#        self.drop_rate_add_count = {}
#
#    def appendDungeonHistory(self, dgn_his_data):
#        dgn_id = dgn_his_data['dungeon_id']
#        self.__dgn_his_list.append(dgn_his_data)
#        self.__dgn_his_dic[ dgn_id ] = dgn_his_data
#
#    def checkDayChange(self, cur_time):
#        cur_date = time.strftime('%Y-%m-%d', time.localtime(cur_time))
#        log.debug('[ checkDayChange ] cur_date:', cur_date, ' cur time:', cur_time)
#
#        for dd in self.__dgn_his_list:
#            dungeon_id = dd['dungeon_id']
#            last_time = dd['dungeon_last_challenge_time']
#            last_date = time.strftime('%Y-%m-%d', time.localtime(last_time))
#            log.debug('[ checkDayChange ] cid {0}, dgn {1}, last_datetime {2}, last time {3}'.format( self.cid, dungeon_id, last_date, last_time ))
#            if last_date != cur_date and 0 != dd['dungeon_today_challenge']:
#                log.debug(' Reset today challenge of dgn ', dungeon_id, ' cid ', self.cid)
#                dd['dungeon_today_challenge'] = 0
#
#    def getDungeonHistoryList(self):
#        return self.__dgn_his_list
#
#    def getDungeonHistoryCount(self):
#        return len(self.__dgn_his_list)
#
#    def getSceneStar(self):
#        star = 0
#        for dd in self.__dgn_his_list:
#            star += dd['dungeon_star']
#        return star
#
#    def getBriefHistory(self):
#        return self.brief_history
#
#    def getDropRateAddCount(self, drop_id):
#        return self.drop_rate_add_count.get(drop_id, 0)
#
#    def setDropRateAddCount(self, drop_id, add_count):
#        if add_count <= 0:
#            if self.drop_rate_add_count.has_key( drop_id ):
#                del self.drop_rate_add_count[drop_id]
#        else:
#            self.drop_rate_add_count[drop_id] = add_count
#
#    def getDungeonHistory(self, dungeon_id):
#        if dungeon_id in self.__dgn_his_dic:
#            return self.__dgn_his_dic[ dungeon_id ]
#        else:
#            return None
#
#    def sync(self):
#        log.debug('Sync user adv history::cid:{0}, town:{1}, dgn-his-count:{2}'.format( self.cid, self.town_id, len(self.__dgn_his_list) ) )
#        redis.hset( FELLOW_TOWN_ADV_HISTORY % self.town_id, 
#                   self.cid,
#                   dumps( (self.cid, self.town_id, self.brief_history, self.__dgn_his_list) )
#        )
#        redis.hset( MONSTER_DROP_HISTORY % self.town_id, self.cid, dumps( self.drop_rate_add_count) )
#
#    @staticmethod
#    def load(cid, town_id):
#        data = redis.hget( FELLOW_TOWN_ADV_HISTORY % town_id, cid )
#        his = TownAdventureHistory(cid, town_id)
#        if data:
#            cid, town_id, brief_history, __dgn_his_list = loads( data ) 
#
#            his.brief_history = brief_history
#            his.__dgn_his_list = __dgn_his_list
#
#            for dd in his.__dgn_his_list:
#                dgn_id = dd['dungeon_id']
#                his.__dgn_his_dic[ dgn_id ] = dd
#                #log.debug('  Load dgn his:', dd)
#            log.debug('Load user adv history XXXXX cid:{0}, town:{1}, dgn-his-count:{2}'.format( his.cid, his.town_id, len(his.__dgn_his_list) ) )
#        else:
#            log.debug('New user adv history XXXXX cid:{0}, town:{1}, dgn-his-count:{2}'.format( his.cid, his.town_id, len(his.__dgn_his_list) ) )
#
#        drop_data = redis.hget( MONSTER_DROP_HISTORY % town_id, cid )
#        if drop_data:
#            his.drop_rate_add_count = loads( drop_data )
# 
#        return his
#
#class TownAdventureHistoryMgr(object):
#    ''' Star: 0-simple 1-middle 2-difficulty -1未开始
#    '''
#    def __init__(self, cid):
#        self.cid = cid
#        self.__dic_scene_history = {}#k:TownID v:TownAdventureHistory
#
#    def sync(self):
#        log.debug('TownAdventureHistoryMgr::sync start. cid {0}.'.format(self.cid))
#        list_town_id = []
#        for town_id in self.__dic_scene_history.iterkeys():
#            list_town_id.append(town_id)
#
#        redis.hset( FELLOW_TOWN_ADV_LIST, self.cid, dumps(list_town_id) )
#        log.debug('TownAdventureHistoryMgr::sync, list-town-id:',  list_town_id)
#
#        for town_his in self.__dic_scene_history.itervalues():
#            town_his.sync()
#
#    def load(self):
#        log.debug('TownAdventureHistoryMgr::load start. cid {0}.'.format(self.cid))
#        self.__dic_scene_history = {}
#
#        data = redis.hget( FELLOW_TOWN_ADV_LIST, self.cid )
#        if data:
#            list_town_id = loads( data )
#            log.debug('TownAdventureHistoryMgr::load, length: {0}, list-town-id:{1}',  list_town_id)
#            if isinstance(list_town_id, list):
#                for town_id in list_town_id:
#                    tah = TownAdventureHistory.load( self.cid, town_id )
#                    self.__dic_scene_history[town_id] = tah
#                    log.debug('Load town adv his, cid {0}, town {1}'.format( self.cid, town_id ))
#            else:
#                log.error('Load list_town_id fail! cid:', self.cid)
#        else:
#            log.debug('Town adv list of cid {0} is empty.'.format(self.cid))
#
#    def getTownHistory(self, town_id):# Return: None or TownAdventureHistory
#        if town_id in self.__dic_scene_history:
#            return self.__dic_scene_history[town_id]
#        else:
#            return None
#
#    def getDungeonHistory(self, dungeon_id):#Return: None or DungeonHistory( { fn : value, ...} )
#        dungeon_cfg = g_TownCfgMgr.getDungeonCfg(dungeon_id)
#        if not dungeon_cfg:
#            log.debug('Can not find dungeon cfg:', dungeon_id)
#            return None
#
#        scene_id = dungeon_cfg['TownID']
#        town_adv_his = self.getTownHistory(scene_id)
#        if not town_adv_his:
#            log.error('Can not find town history. scene {0}'.format(scene_id))
#            return None
#
#        return town_adv_his.getDungeonHistory(dungeon_id)
#
#    def createTownHistory(self, town_id):#Return: TownAdventureHistory
#        log.debug('Create history of town ', town_id)
#        if town_id in self.__dic_scene_history:
#            return self.__dic_scene_history[town_id]
#        else:
#            town_his = TownAdventureHistory(self.cid, town_id)
#            self.__dic_scene_history[town_id] = town_his
#
#            list_dgn_data = g_TownCfgMgr.getDungeonListInTown(town_id)
#            for dd in list_dgn_data:
#                dgn_id = dd['DungeonID']
#                dgn_his_data = {}
#                dgn_his_data['dungeon_id'] = dgn_id
#                dgn_his_data['dungeon_star'] = 0 # 初始值为-1
#                dgn_his_data['dungeon_today_challenge'] = 0
#                dgn_his_data['dungeon_last_challenge_time'] = 0
#                town_his.appendDungeonHistory( dgn_his_data )
#                log.debug('  his of dgn ', dgn_id)
#        return town_his
#
#    def getPassedFlagOfTown(self, town_id):#Return: Bool
#        #list_dgn_data = g_TownCfgMgr.getDungeonListInTown(town_id)
#
#        town_his = self.getTownHistory(town_id)
#        if not town_his:
#            return False
#        else:
#            if 0 == len(town_his.getDungeonHistoryList()):
#                log.error('Length of dungeon-his-list is 0! town {0}, cid {1}'.format( town_id, self.cid ))
#                return False
#            for dgn_his in town_his.getDungeonHistoryList():
#                #dgn_id = dgn_his['dungeon_id']
#                # Star: 0-simple 1-middle 2-difficulty
#                if 0 > dgn_his['dungeon_star']:
#                    return False
#            return True
#
#    def getStarOfTown(self, town_id):#Return: int
#        list_dgn_data = g_TownCfgMgr.getDungeonListInTown(town_id)
#        star_amount = 0
#        town_his = self.getTownHistory(town_id)
#        if not town_his:
#            return 0
#        else:
#            town_his = self.getTownHistory(town_id)
#            if 0 == len(town_his.getDungeonHistoryList()):
#                log.error('Length of dungeon-his-list is 0! town {0}, cid {1}'.format( town_id, self.cid ))
#                return 0
#            for dgn_his in town_his.getDungeonHistoryList():
#                dgn_star = dgn_his['dungeon_star'] 
#                if 0 != dgn_star:
#                    star_amount += dgn_star
#        return star_amount

