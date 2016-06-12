#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
from twisted.internet import reactor, protocol, defer
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements


class StrBodyProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class Response(object):
    def __init__(self, attribs):
        if isinstance(attribs, dict):
            self.__dict__.update(attribs)
        else:
            self.value = attribs

    def __str__(self):
        return '<Response>%s' % str(self.__dict__)

    def __repr__(self):
        return '<Response>%s' % str(self.__dict__)


class ResponseBodyReceiver(protocol.Protocol):
    def __init__(self, d):
        self.d = d
        self.body = ''

    def dataReceived(self, bytes):
        self.body = bytes

    def connectionLost(self, reason):
        if self.body:
            self.d.callback(self.body)
        else:
            self.d.errback(Exception('[ResponseBodyReceiver]No body received.'))

        self.body = ''


class HttpRequestHelper(object):
    def __init__(self, reactor=reactor):
        self.agent = Agent(reactor)

    def request(self, url, method='GET', data=None):
        d = defer.Deferred()
        _headers = {}
        headers = None

        if method == 'GET':
            data = None
        elif method == 'POST':
            _headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            d.errback(Exception('Not Support Method:%s.' % method))
            return

        if _headers:
            headers = Headers()
            for k, v in _headers.iteritems():
                headers.setRawHeaders(urllib.quote(k), [urllib.quote(v)])

        if data:
            data = StrBodyProducer(data)
        #print 'Req url:', url, ' Head:', headers
        self.agent.request(
                method,
                url,
                headers,
                data).addCallback(self.received, d).addErrback(
                    self.errback, d)

        return d

    def received(self, res, d):
        if res.code == 200:
            res.deliverBody(ResponseBodyReceiver(d))
            return d
        else:
            d.errback(Exception('[HttpRequestHelper]Http response status error. code:%s.' % res.code))

    def errback(self, error, d):
        d.errback(error)
