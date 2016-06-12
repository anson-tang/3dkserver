#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

from time               import time
from urllib             import urlencode
from twisted.internet   import defer
from hashlib            import md5
from json               import loads

from rpc                import route
from protocol_manager   import gs_call
from log                import log
from manager.gateuser   import g_UserMgr
from syslogger          import syslogger
from errorno            import GIFT_CODE_FAILURE
from constant           import TIPCAT_LOCAL_OSS_URLBASE, TIPCAT_ONLINE_OSS_URLBASE, TIPCAT_CID, TIPCAT_OSS_SECURITY_ID, LOG_GIFT_CODE_USE


from http               import HttpRequestHelper
httphelper = HttpRequestHelper()


OSS_RETURN_CODE = {
             1: 0, # 兑换成功
        -10000: 151, # 兑换失败 系统错误
            -1: 151, # 兑换失败 参数错误
            -2: 151, # 兑换失败 key配置错误
            -3: 151, # 兑换失败 签名错误
            -4: 151, # 兑换失败 存储过程错误
        -10001: 151, # 兑换失败 游戏服务器不存在
        -10002: 151, # 兑换失败 合作商不存在
        -10003: 152, # 兑换码不存在 兑换码不存在
        -10004: 152, # 兑换码不存在 批次号不存在
        -10011: 152, # 兑换码不存在 批次号已删除
        -10012: 153, # 兑换码已使用
        -10013: 155, # 批次号已使用
        -10014: 154, # 批次号已过期
        -10021: 156, # 兑换码不能在这个游戏服务器上使用
        -10022: 157, # 兑换码不能在这个混服渠道上使用
        }

def oss_gift_code_url(base_url, platform_id, giftcode, game_server_id, cid):
    ts = int(time())
    sign_before_encode = '{0}{1}{2}{3}{4}{5}'.format(game_server_id, platform_id, cid, giftcode, ts, TIPCAT_OSS_SECURITY_ID)
    sign = md5(sign_before_encode).hexdigest()[3:27]

    q = urlencode(dict(game=game_server_id, partner=platform_id, character=cid, giftcode=giftcode, timestamp=ts, sign=sign))
    return '%s?%s' % (base_url, q)

@route()
@defer.inlineCallbacks
def use_gift_code(p, req):
    ''' 使用兑换码
    @param: platform_id-合作商ID。1:tipcat, 其它...
    @param: giftcode-兑换码序列号
    @param: game_server_id-OSS中服务器管理对应的游戏服务器ID
    '''
    errorno = GIFT_CODE_FAILURE
    response, url, cid, return_code, errorno = '', '', 0, 0, 0
    platform_id, giftcode, game_server_id = int(req[0]), req[1], int(req[2])

    if platform_id is None:
        log.error('OSS PARAM ERROR. request: {0}.'.format( req ))
        defer.returnValue( (errorno, '') )

    # 除了tipcat外 就是heitao
    if platform_id == TIPCAT_CID:
        base_url = TIPCAT_LOCAL_OSS_URLBASE
    else:
        base_url = TIPCAT_ONLINE_OSS_URLBASE

    try:
        cid = p.cid
        url = oss_gift_code_url(base_url, platform_id, giftcode, game_server_id, cid)
        #log.info('For Test. url: {0}.'.format( url ))
        gift_id  = 0
        response = yield httphelper.request(url, 'POST')
        response = loads(response)
        #log.info('For Test. response: {0}.'.format( response ))
        return_code = int(response['return_code'])
        if return_code <= 0:
            log.error('OSS GIFTCODE ERROR. cid: {0}, request: {1}, response: {2}, url: {3}.'.format( cid, req, response, url ))
            errorno = OSS_RETURN_CODE.get(return_code, GIFT_CODE_FAILURE)
        else:
            gift_id = int(response['gift_id'])
            errorno = yield gs_call('new_award_to_center', (cid, gift_id))
            if errorno:
                log.error('Unknown gift_id ERROR. cid: {0}, request: {1}, response: {2}, url: {3}.'.format( cid, req, response, url ))

        user = g_UserMgr.getUserByCid( cid )
        if user and user.info:
            syslogger(LOG_GIFT_CODE_USE, cid, user.info['level'], user.info['vip_level'], 0, giftcode, gift_id, return_code, errorno)
        else:
            syslogger(LOG_GIFT_CODE_USE, cid, 0, 0, 0, giftcode, gift_id, return_code, errorno)
        defer.returnValue( (errorno, '') )
    except Exception as e:
        log.error('OSS GIFTCODE ERROR. cid: {0}, request: {1}, response: {2}.'.format( cid, req, response ))
        log.exception()
        defer.returnValue( (errorno, '') )



