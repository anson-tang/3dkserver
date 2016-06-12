from models.lover_kiss import LoverKissMgr

from log      import log
from time     import time
from rpc      import route
from errorno  import *
from constant import *
from manager.gsuser import g_UserMgr
from twisted.internet    import defer


@route()
@defer.inlineCallbacks
def lover_kiss_get_info(p, req):
    '''
    get activity info
    '''
    res = CONNECTION_LOSE

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        _mgr = yield LoverKissMgr.get(user)
        if _mgr:
            res = yield _mgr.value_t
        else:
            log.error('user not existed!')

    defer.returnValue(res)

@route()
@defer.inlineCallbacks
def lover_kiss_touch_beauty(p, req):
    '''
    touch beautiful girl
    '''
    res = CONNECTION_LOSE

    cid, [t_type, location] = req

    user = g_UserMgr.getUser(cid)
    if user:
        _mgr = yield LoverKissMgr.get(user)
        if _mgr:
            b = _mgr.check_touch(location, t_type)
            if b:
                res = yield _mgr.get_touch_reward(location)
            else:
                res = [[], _mgr.opened_list, _mgr.normal_rose, _mgr.blue_rose, BLUE_ROSE_MAX_NUM - _mgr.extra_blue_rose]
        else:
            log.error('user not existed!')
    defer.returnValue(res)

@route()
@defer.inlineCallbacks
def lover_kiss_refresh(p, req):
    '''
    refresh activity
    '''
    res = CONNECTION_LOSE

    cid, = req

    l = []
    user = g_UserMgr.getUser(cid)
    if user:
        _mgr = yield LoverKissMgr.get(user)
        if _mgr:
            _mgr.refresh_box()
            res = yield _mgr.value_t
            for r in res:
                l.append(r)
            l.append(user.credits)
            res = l
        else:
            log.error('user not existed!')

    defer.returnValue(res)


