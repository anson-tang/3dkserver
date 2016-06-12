#!/usr/bin/env python
#-*-coding: utf-8-*-

# Version: 0.1
# Author: Don Li <donne.cn@gmail.com>
# License: Copyright(c) 2013 Don.Li
# Summary: 

import os, sys

current_path = os.path.abspath( os.path.dirname( __file__ ) )
db_path      = current_path + '/sql/'
all_db       = 'sysconfig', 'userdb'

from datetime import datetime

def walk_db_fils( db, begin_date ):
    result = ''

    if db == 'sysconfig':
        result += open( db_path + 'tc3dk_sysconfig.sql' ).read() + os.linesep 

    all_files = os.listdir( db_path )

    db_files = []


    for f  in all_files:
        fname, ext = os.path.splitext( f )
        if ext == '.sql':
            try:
                db_name, year, month, day = fname.split( '_' )
                f_date = datetime( int(year), int(month), int(day) )

                if db_name == db and f_date > begin_date:
                    db_files.append((f_date, f))
            except ValueError:
                continue
            except:
                raise

    db_files.sort()

    for _, f in db_files:
        result += open( db_path + f ).read() + os.linesep 

    return result


def begin_datetime():
    _begin_y, _begin_m, _begin_d = 2013, 2, 1

    _last_log_file = '/tmp/syncqa_time'
    if os.path.isfile( _last_log_file ):
        _last_log = open( _last_log_file ).read().split()
        if len( _last_log ) == 3:
            _begin_y, _begin_m, _begin_d = map( int, _last_log )

    return datetime( _begin_y, _begin_m, _begin_d )

def main():
    if len( sys.argv ) != 3:
        print 'Usage: python combine_db.py <DESTPATH> <DB>'
        sys.exit(1)
    else:
        dest_path   = sys.argv[1].strip()
        db          = sys.argv[2].strip()
        _, _db, _ = db.split('_')

        if _db not in all_db:
            print 'Un-supported db:', _db
            sys.exit(1)
        else:
            db_no  = all_db.index( _db ) + 1
            d      = begin_datetime()
            dest_f = '{0}/{1}'.format( dest_path, db )
            print 'begin time:', d, 'dest_f:', dest_f

            all_sql = walk_db_fils( _db, d )
            open( dest_f, 'w' ).write( all_sql )

if __name__ == '__main__' : main()
