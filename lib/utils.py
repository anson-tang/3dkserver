#-*-coding: utf-8-*-

'''
@version: 0.2
@author: U{Don.Li<mailto: donne.cn@gmail.com>}
@license: Copyright(c) 2012 Don.Li

@summary:
'''

import traceback
import urllib2, json

from datetime import datetime, timedelta
from base64 import urlsafe_b64encode
from bisect import bisect
from hashlib import md5
import hmac
from os import urandom
from time import time, mktime, strftime, localtime
import random

import log

def pprint(*args):
    import sys 
    sys.stderr.write(', '.join((str(arg) for arg in args)) + '\n')

def print_e():
    pprint(traceback.format_exc())       

def datetime2time(d_time):
    if not d_time:
        return 0
    return int(mktime(d_time.timetuple()))

def timestamp2string(timestamp):
    if (not timestamp) or (not isinstance(timestamp, int)):
        return timestamp
    return strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp))

def datetime2string(d_time=None):
    if not d_time:
        d_time = datetime.now()
    return d_time.strftime("%Y-%m-%d %H:%M:%S")

def string2datetime(string):
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def get_reset_timestamp(reset_hours=0):
    ''' 返回每日0点的时间戳用于判断数据是否需要清零 '''
    _now = datetime.now()
    if _now.hour < reset_hours:
        _now += timedelta(days=-1)

    reset_datetime = _now.replace(_now.year, _now.month, _now.day, reset_hours, 0, 0)

    return int(mktime(reset_datetime.timetuple()))

def get_reward_timestamp(hours=22, minutes=0, seconds=0):
    ''' 返回每日22点的时间戳用于判断数据是否需要结算 '''
    _now = datetime.now()
    if _now.hour >= hours and _now.minute >= minutes and _now.second >= seconds:
        _now += timedelta(days=1)

    _datetime = _now.replace(_now.year, _now.month, _now.day, hours, minutes, seconds)

    return int(mktime(_datetime.timetuple()))

def get_joust_reward_timestamp(need_week=6, need_hours=23, need_mins=0):
    ''' 返回下一个结算时间点 每周六23点 '''
    _dt_now  = datetime.now()
    _weekday = _dt_now.isoweekday()
    _delta_days = 0
    if _weekday < need_week:
        _delta_days = need_week - _weekday
    elif _weekday == need_week:
        if _dt_now.hour < need_hours:
            _delta_days = 0
        else:
            _delta_days = 7
    else:
        _delta_days = need_week

    _dt_now += timedelta(days=_delta_days)
    _datetime = _dt_now.replace(_dt_now.year, _dt_now.month, _dt_now.day, need_hours, need_mins, 0)
    #print 'week: ', need_week, 'hours: ', need_hours, 'next_datetime', _datetime
    return int(mktime(_datetime.timetuple()))

def get_next_timestamp(need_week=6, need_hours=23, need_mins=0):
    ''' 返回下一个结算时间点 每周六23点 '''
    _dt_now  = datetime.now()
    _weekday = _dt_now.isoweekday()
    _delta_days = 0
    if _weekday < need_week:
        _delta_days = need_week - _weekday
    elif _weekday == need_week:
        if _dt_now.hour < need_hours:
            _delta_days = 0
        elif _dt_now.hour == need_hours:
            if _dt_now.minute < need_mins:
                _delta_days = 0
            else:
                _delta_days = 7
        else:
            _delta_days = 7
    else:
        _delta_days = need_week

    _dt_now += timedelta(days=_delta_days)
    _datetime = _dt_now.replace(_dt_now.year, _dt_now.month, _dt_now.day, need_hours, need_mins, 0)
    #print 'week: ', need_week, 'hours: ', need_hours, 'next_datetime', _datetime
    return int(mktime(_datetime.timetuple()))

def get_next_refresh_hour(timestamp):
    ''' 用于神秘商店, 每2小时可获得一次免费刷新次数 '''
    _now     = datetime.now()
    _hour    = _now.hour%2 if _now.hour%2 else 2
    _next_dt = _now + timedelta(hours=_hour, minutes=-_now.minute, seconds=-_now.second, microseconds=-_now.microsecond)
    _d_time  = datetime.fromtimestamp( timestamp )
    #pprint('For Test. _next_dt: {0}, _d_time: {1}, _now: {2}.'.format( _next_dt, _d_time, _now ))
    _base_time = datetime.fromtimestamp(0)
    _count = ((_now.date()-_base_time.date()).days*12+_now.hour/2) - ((_d_time.date()-_base_time.date()).days*12+_d_time.hour/2)

    return int(mktime(_next_dt.timetuple())), _count

def check_valid_time(timestamp, hour=0):
    ''' 检查timestamp是否已超过期限
    @return 0-valid 1-unvalid 
    '''
    _now    = datetime.now()
    _d_time = datetime.fromtimestamp( timestamp ) + timedelta(hours=hour)
    _delta  = _d_time - _now
    return 0 if _delta.total_seconds() > 0 else 1

def timestamp_is_today(last_timestamp):
    ''' return 0-diff date 1-same today '''
    cur_date  = datetime.now().date()
    last_date = datetime.fromtimestamp( last_timestamp ).date()
    return 1 if last_date == cur_date else 0

def timestamp_is_week(last_timestamp):
    ''' return 0-同一天 1-隔天 2-隔周 '''
    _dt_now  = datetime.now()
    _dt_last = datetime.fromtimestamp( last_timestamp )
    if _dt_last.date() == _dt_now.date():
        return 0
    now_week  = _dt_now.isocalendar()[:2]
    last_week = _dt_last.isocalendar()[:2]
    if now_week != last_week:
        return 2
    return 1

def check_joust_status(last_timestamp, need_week=6, need_hours=23):
    ''' 用于大乱斗 
    @return: (date, status)
        其中date: 0-同一天 1-隔天 2-隔周
         status: 0-活动中 1-非活动时间 2-活动已结束
    '''
    _dt_now  = datetime.now()
    _weekday = _dt_now.isoweekday()
    if _weekday == 7 or (_weekday == need_week and _dt_now.hour >= need_hours):
        _status = 2
    elif _dt_now.hour < 8 or _dt_now.hour >= need_hours:
        _status = 1
    else:
        _status = 0

    _dt_last = datetime.fromtimestamp( last_timestamp )
    if _dt_last.date() == _dt_now.date():
        return (0, _status)

    now_week  = _dt_now.isocalendar()[:2]
    last_week = _dt_last.isocalendar()[:2]
    if now_week != last_week:
        return (2, _status)
    else:
        return (1, _status)

def split_items(items_string=''):
    ''' string format: 'ItemType:ItemID:ItemNum,ItemType:ItemID:ItemNum' '''
    items = []
    if not items_string:
        return items
    items_data = items_string.split(',')
    for _data in items_data:
        _item = _data.split(':')
        try:
            items.append( tuple(map(int, _item)) )
        except:
            print items_string, items, _item

    return tuple(items)

def http_json_get_sync(url, params):
    if isinstance(params, dict):
        params = '&'.join(['{0}={1}'.format(k, v) for k, v in params.iteritems()])

    url += '?' + params
    pprint('[ http_json_get_sync ]', url)
    req = urllib2.Request(url)
    return json.loads(urllib2.urlopen(req).read())


def to_string(i):
    if type(i) == unicode:
        return i.encode('utf-8')
    else:
        return str(i)

def gen_salt(*a):
    m = md5()
    for i in a:
        m.update(to_string(i))
    return m.hexdigest()


def gen_hmac(*a):
    h = hmac.new(TIPCAT_SECURITY_ID)
    for i in a:
        h.update(to_string(i))
    return h.hexdigest()


def gen_passwd(n=32):
    return urlsafe_b64encode(urandom(n))[:n]

def get_previous_value(basic_value, list_value):
    '''在list_value中查找比basic_value小的最接近的值
    '''
    while basic_value not in list_value:
        basic_value -= 1
        if basic_value < 0:
            return None
        if basic_value in list_value:
            break
    return basic_value


class MockTransport(object):
    def write(self, data):
        log.debug('[ MockTransport.write ]data:', data)

    def getPeer(self):
        return 'MockTransport<%s>' % id(self)

class MockProtocol(object):
    transport = MockTransport()

def mock_println(res):
    from twisted.python.failure import Failure
    if isinstance(res, Failure):
        print '[ mock ]exception: {0}'.format(res.getTraceback())
    else:
        print '[ mock ]result: {0}'.format(res)

def mock(func, request):
    from twisted.internet.defer import maybeDeferred
    from rpc import get_handler

    handler, _ = get_handler(func)
    maybeDeferred(handler, MockProtocol(), request).addBoth(mock_println)

def rand_num(total=10000):
    return random.randint(0, total-1)
