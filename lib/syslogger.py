#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

#import gevent
import socket
import atexit
import sys 


CRITICAL = 6
ERROR    = 5
WARNING  = 4
NOTICE   = 3
INFO     = 2
DEBUG    = 1
NOTSET   = 0

def pprint(*args):
    sys.stderr.write(', '.join((str(arg) for arg in args)) + '\n')

class SysLogger(object):
    # priorities
    LOG_EMERG     = 0       #  system is unusable
    LOG_ALERT     = 1       #  action must be taken immediately
    LOG_CRIT      = 2       #  critical conditions
    LOG_ERR       = 3       #  error conditions
    LOG_WARNING   = 4       #  warning conditions
    LOG_NOTICE    = 5       #  normal but significant condition
    LOG_INFO      = 6       #  informational
    LOG_DEBUG     = 7       #  debug-level messages

    # facility codes
    LOG_KERN      = 0       #  kernel messages
    LOG_USER      = 1       #  random user-level messages
    LOG_MAIL      = 2       #  mail system
    LOG_DAEMON    = 3       #  system daemons
    LOG_AUTH      = 4       #  security/authorization messages
    LOG_SYSLOG    = 5       #  messages generated internally by syslogd
    LOG_LPR       = 6       #  line printer subsystem
    LOG_NEWS      = 7       #  network news subsystem
    LOG_UUCP      = 8       #  UUCP subsystem
    LOG_CRON      = 9       #  clock daemon
    LOG_AUTHPRIV  = 10      #  security/authorization messages (private)
    LOG_FTP       = 11      #  FTP daemon

    # other codes through 15 reserved for system use
    LOG_LOCAL0    = 16      #  reserved for local use
    LOG_LOCAL1    = 17      #  reserved for local use
    LOG_LOCAL2    = 18      #  reserved for local use
    LOG_LOCAL3    = 19      #  reserved for local use
    LOG_LOCAL4    = 20      #  reserved for local use
    LOG_LOCAL5    = 21      #  reserved for local use
    LOG_LOCAL6    = 22      #  reserved for local use
    LOG_LOCAL7    = 23      #  reserved for local use

    facility_names = {
        'auth':     LOG_AUTH,
        'authpriv': LOG_AUTHPRIV,
        'cron':     LOG_CRON,
        'daemon':   LOG_DAEMON,
        'ftp':      LOG_FTP,
        'kern':     LOG_KERN,
        'lpr':      LOG_LPR,
        'mail':     LOG_MAIL,
        'news':     LOG_NEWS,
        'syslog':   LOG_SYSLOG,
        'user':     LOG_USER,
        'uucp':     LOG_UUCP,
        'local0':   LOG_LOCAL0,
        'local1':   LOG_LOCAL1,
        'local2':   LOG_LOCAL2,
        'local3':   LOG_LOCAL3,
        'local4':   LOG_LOCAL4,
        'local5':   LOG_LOCAL5,
        'local6':   LOG_LOCAL6,
        'local7':   LOG_LOCAL7,
    }

    level_priority_map = {
        DEBUG:      LOG_DEBUG,
        INFO:       LOG_INFO,
        NOTICE:     LOG_NOTICE,
        WARNING:    LOG_WARNING,
        ERROR:      LOG_ERR,
        CRITICAL:   LOG_CRIT
    }

    def __init__(self, address=None, facility='local0', socktype=socket.SOCK_STREAM, level=NOTSET):
        if address is None:
            if sys.platform == 'darwin':
                address = '/var/run/syslog'
            else:
                address = '/dev/log'

        self.address  = address
        self.facility = facility
        self.socktype = socktype
        self.level    = level

        if isinstance(address, basestring):
            self._connect_unixsocket()
        else:
            self._connect_netsocket()

    def _connect_unixsocket(self):
        self.unixsocket = True
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            self.socket.connect(self.address)
        except socket.error:
            self.socket.close()
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(self.address)

    def _connect_netsocket(self):
        self.unixsocket = False
        self.socket = socket.socket(socket.AF_INET, self.socktype)
        if self.socktype == socket.SOCK_STREAM:
            self.socket.connect(self.address)
            #self.address = self.socket.getsockname()

    def encode_priority(self, record):
        facility = self.facility_names[self.facility]
        priority = self.level_priority_map.get(self.level,
                                               self.LOG_WARNING)
        return (facility << 3) | priority

    def write(self, record):
        try:
            self.send_to_socket((u'<%d>:%s\n' % (
                self.encode_priority(record),
                record
            )).encode('utf-8'))
        except Exception, e:
            pprint('write failed. e:{0}.'.format(e))

    def send_to_socket(self, data):
        if self.unixsocket:
            try:
                self.socket.send(data)
            except socket.error:
                self.close()
                self._connect_unixsocket()
                self.socket.send(data)
        elif self.socktype == socket.SOCK_DGRAM:
            # the flags are no longer optional on Python 3
            try:
                self.socket.sendto(data, 0, self.address)
            except socket.error:
                self.close()
                self._connect_netsocket()
                self.socket.sendto(data, 0, self.address)
        else:
            try:
                self.socket.sendall(data)
            except socket.error:
                self.close()
                self._connect_netsocket()
                self.socket.sendall(data)

    def close(self):
        self.socket.close()

default_logger = None

def init_logger(address=('127.0.0.1', 9999)):
    print '============== syslogger address: ', address
    global default_logger

    if not default_logger:
        default_logger = SysLogger(address=address)
        atexit.register(default_logger.close)

def syslogger(*args):
    return
    try:
        default_logger.write(('[%s]' * len(args)) % (args))
        #pprint(args)
    except:
        pprint('Syslogger write log error......')

def main():
    init_logger()

    i = 0
    while i < 10:
        syslogger(i, 2, 3, 4, 5, 1)
        i += 1

if __name__ == '__main__': main()
