#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2015 Don.Li
# Summary: 

from time     import time, mktime, strptime
from log      import log
from errorno  import *
from constant import *
from redis    import redis
from marshal  import loads, dumps     
from utils    import timestamp_is_today
from bisect   import insort_right

from twisted.internet       import defer, reactor
from models.item            import item_add

def str2timestamp(string):
    return int(mktime(strptime(string, '%Y-%m-%d %H:%M:%S')))

class ItemGroup(object):
    def __init__(self, group_id, begin_t, end_t):
        self.group_id = group_id
        self.begin_t  = begin_t
        self.end_t    = end_t

        self.item_list = []

    def append_item(self, shop_id, item_type, item_id, item_num, description, orig_credits,
            credits, limit):
        self.item_list.append((shop_id, item_type, item_id, item_num, description, orig_credits, credits, limit))

    @property
    def is_finish(self):
        _finished = True

        t = int(time())
        if t <= self.end_t:
            _finished = False

        return _finished

    @property
    def is_open(self):
        _open = False

        t = int(time())

        if t >= self.begin_t and t <= self.end_t:
            _open = True

        return _open

    def __cmp__(self, other):
        if self.begin_t > other.begin_t and self.end_t > other.end_t:
            return 1
        elif self.begin_t < other.begin_t and self.end_t < other.end_t:
            return -1
        else:
            return 0

    def __str__(self):
        return 'IGroup<%s,b:%s,e:%s>' % (self.group_id, self.begin_t, self.end_t)
    __repr__ = __str__

class TimeLimitedShopMgr(object):
    def __init__(self):
        self.groups_sorted     = []
        self.current_group_idx = -1

        reactor.callLater(1, self.load)
        #reactor.addSystemEventTrigger('before', 'shutdown', self.sync)

    @defer.inlineCallbacks
    def buyed_count_today(self, cid):
        _buyed_cnt_list = []

        _group = self.current_group()
        if _group and _group.is_open:
            _stream = yield redis.hget(DICT_TIME_LIMITED_SHOP_BUYED, cid)
            if _stream:
                _tuple_all_buyed = loads(_stream)

                for _id, _buyed_cnt, _last_buy_t in _tuple_all_buyed:
                    if timestamp_is_today(_last_buy_t):
                        _buyed_cnt_list.append([_id, _buyed_cnt, _last_buy_t])
        else:
            redis.hdel(DICT_TIME_LIMITED_SHOP_BUYED, cid)

        defer.returnValue(_buyed_cnt_list)

    @defer.inlineCallbacks
    def can_buy(self, user):
        res = 0

        _group = self.current_group()
        if _group and _group.is_open:
            _buyed_list = yield self.buyed_count_today(user.cid)

            if len(_buyed_list) < len(_group.item_list):
                res = 1
            else:
                for _shop_id, _buyed_cnt, _ in _buyed_list:
                    for _item in _group.item_list:
                        if _item[0] == _shop_id and _buyed_cnt < _item[7]:
                            res = 1
                            break # 优化： 只要还有购买次数，不要再继续检查了

                    if res == 1: break # 优化：只要有购买次数，就不用继续遍历
        else: #没有商品组激活或者商品组未开放
            res = 0

        defer.returnValue( res )

    def current_group(self):
        _group = None

        if self.current_group_idx >= 0 and self.current_group_idx < len(self.groups_sorted):
            _group = self.groups_sorted[self.current_group_idx]
            if _group.is_finish:
                while self.current_group_idx < len(self.groups_sorted):
                    _group = self.groups_sorted[self.current_group_idx]
                    if not _group.is_finish: break
                    self.current_group_idx += 1

        return _group

    @defer.inlineCallbacks
    def shop_list(self, user):
        cid = user.cid

        _group = self.current_group()
        if _group:
            _item_list = []
            _buyed_list = yield self.buyed_count_today(cid)

            for _item in _group.item_list:
                shop_id, item_type, item_id, item_num, description, orig_credits, credits, limit = _item

                if _buyed_list:
                    log.debug('buyed list:', _buyed_list)
                    for _id, _buyed_cnt, _ in _buyed_list:
                        if _id == shop_id:
                            _item_list.append((shop_id, item_type, item_id, item_num, description, orig_credits, credits, limit, _buyed_cnt))
                            break
                    else: #不在已购买记录里
                        _item_list.append((shop_id, item_type, item_id, item_num, description, orig_credits, credits, limit, 0))
                else: #不在已购买记录里
                    _item_list.append((shop_id, item_type, item_id, item_num, description, orig_credits, credits, limit, 0))

            defer.returnValue(((_group.begin_t, _group.end_t), _item_list))
        else:
            defer.returnValue(None)

    @defer.inlineCallbacks
    def buy(self, user, shop_id_buy, buy_cnt):
        cid = user.cid

        _group = self.current_group()
        if _group:
            if _group.is_open:
                for _item in _group.item_list:
                    shop_id, item_type, item_id, item_num, description, orig_credits, credits, limit = _item

                    if shop_id == int(shop_id_buy):
                        _buyed_list = yield self.buyed_count_today(cid)

                        if _buyed_list:
                            for _id, _buyed_cnt, _ in _buyed_list:
                                if _id == shop_id_buy and (_buyed_cnt + buy_cnt) > limit:
                                    defer.returnValue((TIME_LIMITED_SHOP_CANNOT_BUY, None))

                        res_consume = yield user.consume_credits(credits * buy_cnt, WAY_TIME_LIMITED_SHOP)
                        if res_consume:
                            defer.returnValue((res_consume, None))

                        _res_add, _items_added = yield item_add(user, ItemType=item_type, ItemID=item_id, ItemNum=item_num * buy_cnt, AddType=WAY_TIME_LIMITED_SHOP)
                        if _res_add:
                            defer.returnValue((_res_add, None))
                        else:
                            _t = int(time())
                            for _item in _buyed_list:
                                if _item[0] == shop_id_buy:
                                    _item[1] += buy_cnt
                                    _item[2] = _t
                                    break
                            else:
                                _buyed_list.append([shop_id, buy_cnt, _t])

                            log.debug('after buy.', _buyed_list)

                            yield redis.hset(DICT_TIME_LIMITED_SHOP_BUYED, cid, dumps(_buyed_list))
                            defer.returnValue((NO_ERROR, (user.credits, _items_added)))
                else:
                    log.error('no such shop id in current group', _group, shop_id_buy)
                    defer.returnValue((TIME_LIMITED_SHOP_NO_SUCH_ITEM, None))
            else:
                log.error('current group is closed.', _group)
                defer.returnValue((TIME_LIMITED_SHOP_CURRENT_GROUP_CLOSED, None))
        else:
            defer.returnValue((TIME_LIMITED_SHOP_ALL_GROUP_CLOSED, None))

    @defer.inlineCallbacks
    def load(self):
        try:
            _l_stream = yield redis.lrange(LIST_TIME_LIMITED_GROUP, 0, -1)
            if _l_stream:
                for i in xrange(len(_l_stream)):
                    _group = loads(_l_stream[i])
                    if not isinstance(_group, (list, tuple)) or len(_group) != 3:
                        log.warn('unknown stream:', _group)
                        continue

                    _group_id, _begin_t, _end_t = loads(_l_stream[i])
                    _group = ItemGroup(_group_id, _begin_t, _end_t)

                    insort_right(self.groups_sorted, _group)

                yield self.load_by_group()
        except Exception, e:
            log.warn(e)
            reactor.callLater(1, self.load)

    @defer.inlineCallbacks
    def refresh_group_by_oss(self, dict_group_config):
        res = 1

        try:
            self.groups_sorted = []
            yield redis.delete(LIST_TIME_LIMITED_GROUP)

            for _group_id, dict_config in dict_group_config.iteritems():
                _group_id = int(_group_id)
                _begin_t, _end_t = str2timestamp(dict_config['begin_time']), str2timestamp(dict_config['end_time'])
                _group = ItemGroup(_group_id, _begin_t, _end_t)

                insort_right(self.groups_sorted, _group)
                yield redis.lpush(LIST_TIME_LIMITED_GROUP, dumps((_group_id, _begin_t, _end_t)))

            yield self.load_by_group()
        except:
            log.exception('dict_group_config:{0}'.format(dict_group_config))
            res = OSS_TIME_LIMITED_SHOP_GROUP_EXCEPTION

        defer.returnValue( res )

    def refresh_item_by_oss(self, list_item_config):
        res = 1

        try:
            for _group in self.groups_sorted:
                _group.item_list = []

            for dict_config in list_item_config:
                _group_id, _shop_id, _item_type, _item_id, _item_num, _description, _orig_credits, _credits, _limit = \
                        int(dict_config['GroupID']), int(dict_config['ID']), int(dict_config['ItemType']), int(dict_config['ItemID']), \
                        int(dict_config['Count']), dict_config['Information'], int(dict_config['OriginalPrice']), \
                        int(dict_config['CurrentPrice']), int(dict_config['LimitNum'])

                for _group in self.groups_sorted:
                    if _group.group_id == _group_id:
                        _group.append_item(_shop_id, _item_type, _item_id, _item_num, _description, _orig_credits, _credits, _limit)
                        break
                else:
                    _now = int(time())
                    _begin_t, _end_t = _now, _now
                    _group = ItemGroup(_group_id, _begin_t, _end_t)
                    _group.append_item(_shop_id, _item_type, _item_id, _item_num, _description, _orig_credits, _credits, _limit)

                    insort_right(self.groups_sorted, _group)
                    redis.lpush(LIST_TIME_LIMITED_GROUP, dumps((_group_id, _begin_t, _end_t)))

            self.sync()
        except:
            log.exception('list_item_config:{0}'.format(list_item_config))
            res = OSS_TIME_LIMITED_SHOP_GROUP_EXCEPTION

        return res

    @defer.inlineCallbacks
    def load_by_group(self):
        for idx, _group in enumerate(self.groups_sorted):
            if not _group.is_finish:
                self.current_group_idx = idx
                break

        _l_stream = yield redis.lrange(LIST_TIME_LIMITED_SHOP, 0, -1)
        if _l_stream:
            for i in xrange(len(_l_stream)):
                _item = loads(_l_stream[i])
                if not isinstance(_item, (tuple, list)) or len(_item) != 9:
                    log.warn('item:', _item)
                    continue

                _group_id, _shop_id, _item_type, _item_id, _item_num, _description, _orig_credits, _credits, _limit = _item

                for _group in self.groups_sorted:
                    if _group.group_id == _group_id:
                        _group.append_item(_shop_id, _item_type, _item_id, _item_num, _description, _orig_credits, _credits, _limit)
                        break
                else:
                    log.warn('no group:{0} config for this item.'.format(_group_id))

    def item_list(self):
        _items = []

        for _group in self.groups_sorted:
            _group_items = _group.item_list

            for _g_item in _group_items:
                _item = [_group.group_id]
                _item.extend(list(_g_item))

                if len(_item) > 1:
                    _items.append(_item)

        return _items

    @defer.inlineCallbacks
    def sync(self):
        _v = [dumps(item) for item in self.item_list()]

        if _v:
            yield redis.delete(LIST_TIME_LIMITED_SHOP)
            redis.lpush(LIST_TIME_LIMITED_SHOP, _v)

try:
    timeLimitedShop
except NameError:
    timeLimitedShop = TimeLimitedShopMgr()
