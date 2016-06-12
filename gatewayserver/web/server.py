#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from twisted.web           import http
from twisted.internet      import defer
from log                   import log
from errorno               import *
from web.handler_gm        import gm_cmd
from web.handler_payment   import payment
from web.htpayment         import htpayment
from web.handler_default   import sys_config, reload_sysconfig, sys_keyword, sys_randname, ban_word
from web.handler_resource  import reload_resource



route = {
     '/sysconfig': sys_config,
       '/keyword': sys_keyword,
      '/randname': sys_randname,
       '/banword': ban_word,
        '/reload': reload_sysconfig,
            '/gm': gm_cmd,
       '/payment': payment,
     '/htpayment': htpayment,
      '/resource': reload_resource,
}

def handleCompleted(response, self):
    self.write(response)
    self.finish()

def error(failure, self):
    log.error('Web process fail! err msg:', failure.getTraceback())
    self.write( json.dumps(UNKNOWN_ERROR) )
    self.finish()

def process(self):
    #from log import log
    #log.debug('web process, self.path:', self.path, ' - - - - - - - - - - - - - - - - - - - - - - - -')
    handler = route.get(self.path)
    if handler is None:
        self.setResponseCode(http.NOT_FOUND)
    else:
        defer.maybeDeferred(handler, self).addCallback(handleCompleted, self).addErrback(error, self)
        #self.write(handler(self))
    #self.finish()
