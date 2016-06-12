#-*-coding:utf-8-*-

import hashlib

CONTENT_TYPE = { 
        '.js':'application/x-javascript',
        '.tar.gz':'application/x-tar',
        '.ico':'image/x-icon',
        '.css':'text/css'
    }   

def content_type(ext):
    return CONTENT_TYPE.get(ext, 'application/octet-stream')
def current_time(f = "%Y-%m-%d %H:%M:%S"):
    from datetime import datetime
    return datetime.now().strftime(f)

try:
    BASE_SESSION_HASH
except NameError:
    BASE_SESSION_HASH = hashlib.md5()
    BASE_SESSION_HASH.update('w2LKSDjjlsdli99uoj#@#')

def gm_sign(*args):
    h = BASE_SESSION_HASH.copy()
    h.update(''.join(map(str, args)))
    return h.hexdigest()
