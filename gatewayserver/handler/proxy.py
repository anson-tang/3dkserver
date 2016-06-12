#!/usr/bin/env python
#-*- coding: utf-8-*-

from rpc     import route
from errorno import *

from twisted.internet.defer import inlineCallbacks, returnValue
from log                    import log
from protocol_manager       import gs_call, ms_call, alli_call

import traceback

PREFIX_FORWARD_TO_CHAT = 'chat'
PREFIX_FORWARD_TO_MAIL = 'mail'
PREFIX_FORWARD_TO_ALLI = 'alliance'

@route(msgid='*')
@inlineCallbacks
def proxy(p, request):
    res = [UNKNOWN_ERROR, None]

    log.info('request: {0}, p: {1}.'.format( request, p ))
    if not (hasattr(p, 'cid') and p.cid):
        res[0] = LOGIN_UNKNOWN_CID
        log.warn('[ proxy ]unknown cid.', request, 'FROM:', p.transport.getPeer())
        returnValue( res )
    else:
        _func, _request = request
        if _request:
            _request = p.cid, _request
        else:
            _request = (p.cid, )

        _prefix = _func.split('_')[0]

        if _prefix == PREFIX_FORWARD_TO_CHAT:
            _call = ms_call
        elif _prefix == PREFIX_FORWARD_TO_MAIL:
            _call = ms_call
        elif _prefix == PREFIX_FORWARD_TO_ALLI:
            _call = alli_call
        else:
            _call = gs_call

        try:
            game_res = yield _call( _func, _request )
        except Exception, e:
            log.error('e: {0}, request: {1}.'.format( e, request ))
            traceback.print_exc()
            returnValue( res )

        if isinstance(game_res, int):
            res[0] = game_res
            returnValue( res )
        else:
            res[0] = NO_ERROR
            res[1] = game_res
            returnValue( res )
        #else:
        #    log.debug('[proxy ]unknown result from', _func, 'result:', game_res)

