from log      import log
from time     import time
from rpc      import route
from errorno  import *
from constant import *
from manager.gsuser import g_UserMgr
from twisted.internet    import defer


@route()
@defer.inlineCallbacks
def get_open_server_quest_info(p, req):
    res = CONNECTION_LOSE

    cid, = req

    user = g_UserMgr.getUser(cid)
    if user:
        res = yield user.open_server_mgr.get_open_server_activity_status()

    defer.returnValue(res)


@route()
@defer.inlineCallbacks
def buy_open_server_reward(p, req):
    res = CONNECTION_LOSE

    cid, [acType, quest_id] = req

    user = g_UserMgr.getUser(cid)
    if user:
        res = yield user.open_server_mgr.buy_open_server_item(acType, quest_id)

    defer.returnValue( res )
