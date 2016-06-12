#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2015 Don.Li
# Summary: 

from time     import time
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     
from utils    import timestamp_is_today

from twisted.internet       import defer, reactor
from models.randpackage     import package_open
from models.item            import item_add
from protocol_manager       import gw_broadcast

from system import get_robot_conf, sysconfig

import random

MAX_RECEIVED_LIST_LEN = 20
NEWYEAR_PACKAGE_ID    = 90001

def robot_name(robot_id):
    _conf = get_robot_conf(robot_id)
    if _conf:
        return _conf['RobotName']

ALL_NEWYEAR_PACKAGE_CREDITS = []
def rand_credits_from_newyear_package():
    global ALL_NEWYEAR_PACKAGE_CREDITS

    if not ALL_NEWYEAR_PACKAGE_CREDITS:
        for package_id, confs in sysconfig['package'].iteritems():
            if package_id == NEWYEAR_PACKAGE_ID:
                for conf in confs[0]:
                    ALL_NEWYEAR_PACKAGE_CREDITS.append(conf['ItemNum'])

    return random.choice(ALL_NEWYEAR_PACKAGE_CREDITS)

class NewYearPackageMgr(object):
    def __init__(self):
        self.received_character_list = []
        self.robots_list             = []

        self.robot_id = 1

        reactor.callLater(1, self.load)
        reactor.addSystemEventTrigger('before', 'shutdown', self.sync)

    @staticmethod
    @defer.inlineCallbacks
    def received_today(cid):
        _received = False

        _stream = yield redis.hget(DICT_NEWYEAR_PACKAGE, cid)
        if _stream:
            _last_recv_t = int(_stream)
            _received = timestamp_is_today(_last_recv_t)

        defer.returnValue(_received)

    @defer.inlineCallbacks
    def receive(self, user):
        cid = user.cid

        _recved = yield newYearPackage.received_today( cid )
        if _recved:
            defer.returnValue((NEWYEAR_PACKAGE_RECEIVED_ALREADY, None))

        _item_rand = yield package_open(user, NEWYEAR_PACKAGE_ID)
        if _item_rand:
            user_item_id = 0
            _item_type, _item_id, _item_num, _notice = _item_rand
            _res = yield item_add(user, ItemType=_item_type, ItemID=_item_id, ItemNum=_item_num, AddType=WAY_NEW_YEAR_PACKAGE)

            self.received_character_list.append((user.lead_id, user.nick_name, _item_num))
            redis.hset(DICT_NEWYEAR_PACKAGE, cid, int(time()))

            if _notice:
                message = RORATE_MESSAGE_ACHIEVE, (ACHIEVE_TYPE_OPEN_NEWYEAR_PACKAGE, (user.nick_name, _item_num))
                gw_broadcast('sync_broadcast', (message, ))

            defer.returnValue((NO_ERROR, (user_item_id, _item_type, _item_id, _item_num)))
        else:
            defer.returnValue((UNKNOWN_ERROR, None))

    @defer.inlineCallbacks
    def load(self):
        try:
            _l_stream = yield redis.lrange(LIST_NEWYEAR_RECEIVED_CHAR, 0, -1)
            if _l_stream:
                for i in xrange(min(MAX_RECEIVED_LIST_LEN, len(_l_stream))):
                    item = _l_stream[i]
                    self.received_character_list.append(loads(item))

            self.adjust_with_robots()
        except Exception, e:
            log.error('Load error. e:{0}.'.format( e ))
            #reactor.callLater(1, self.load)
    @property
    def received_list(self):
        return (self.robots_list + self.received_character_list)[-20:]

    def adjust_with_robots(self):
        _i = MAX_RECEIVED_LIST_LEN - len(self.received_character_list)

        self.robots_list = []

        while _i > 0:
            _robot_name = robot_name(self.robot_id)
            if not _robot_name: continue

            _robot_credits = rand_credits_from_newyear_package()

            self.robots_list.append((random.randint(1, 2), _robot_name, _robot_credits))

            _i            -= 1
            self.robot_id += 1

            if self.robot_id > 5000:
                self.robot_id = 1

        reactor.callLater(3600, self.adjust_with_robots)

    def sync(self):
        _v = [dumps(item) for item in self.received_character_list][:20]

        if _v:
            redis.lpush(LIST_NEWYEAR_RECEIVED_CHAR, _v)
try:
    newYearPackage
except NameError:
    newYearPackage = NewYearPackageMgr()
