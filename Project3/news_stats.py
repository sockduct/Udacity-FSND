#!/usr/bin/env python3
# -*- coding: ascii -*-
# Default is ascii - explicitly coding, could also consider utf-8, latin-1, cp1252, ...
####################################################################################################
#
# Python version(s) used/tested:
# * Python 3.5.2-32 on Linux (Ubuntu 16.04.2 LTS)
#
# Template version used:  0.1.1
#
#---------------------------------------------------------------------------------------------------
#
# Issues/PLanned Improvements:
# * None yet...
#
'''Project 3 - Log Analysis, Analyze fictitious news site to answer statistics questions
'''

# Imports
from collections import namedtuple
import datetime
import psycopg2
import sys

# Globals
# Note:  Consider using function/class/method default parameters instead of global constants where
# it makes sense
#BASE_FILE = 'file1'

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james.r.small@oatt.com'
__date__ = 'June 20, 2017'
__version__ = '0.0.1'


def get_query(crsr, qry, cols=None):
    '''Execute query against database connection and print results'''
    crsr.execute(qry)
    rows = crsr.fetchall()
    title_print = True

    for row in rows:
        if cols:
            if cols.quote:
                h1_len = cols.h1_len + 2
                row0 = '"' + row[0] + '"'
            else:
                h1_len = cols.h1_len
                row0 = row[0]

            if title_print:
                header1 = cols.header1 + ':'
                print('{:>{width1}} -- Number of {}:'.format(header1, cols.header2,
                                                             width1=h1_len))
                title_print = False

            print('{:>{width1}} -- {:>{width2},} {}'.format(row0, row[1], cols.header2,
                                                            width1=h1_len, width2=cols.h2_len))
        else:
            print('row:  {} ({})'.format(row, type(row)))

    # Print an empty line
    print('')

def main(args):
    '''Open connection to database, define queries, call for results'''
    dbconn = psycopg2.connect('dbname=news')
    crsr = dbconn.cursor()
    rec = namedtuple('rec', ['count', 'quote', 'header1', 'header2', 'h1_len', 'h2_len'])

    q1 = '''select articles.title, count(*) as num from articles, log
            where articles.slug = regexp_replace(log.path, '^.*/', '')
            group by articles.title order by num desc limit 3;'''
    row_rec = rec(2, True, 'Article', 'Views', 34, 7)
    get_query(crsr, q1, row_rec)

    q2 = """select authors.name, count(*) as num from authors, articles, log
            where authors.id = articles.author and articles.slug = 
            regexp_replace(log.path, '^.*/', '')  group by authors.name order by num desc;"""
    row_rec = rec(2, False, 'Author', 'Views', 22, 7)
    get_query(crsr, q2, row_rec)

    q3a = '''select min(time) from log;'''
    crsr.execute(q3a)
    current = start = crsr.fetchone()[0].date()

    q3b = '''select max(time) from log;'''
    crsr.execute(q3b)
    end = crsr.fetchone()[0].date()

    title_print = True
    while True:
        q3c_start = current.isoformat() + ' 00:00:00+00'
        q3c_end = current.isoformat() + ' 23:59:59+00'
        q3c1 = """select count(*) as num from log where time >=
                  '{}' and time <= '{}';""".format(q3c_start, q3c_end)
        crsr.execute(q3c1)
        daily_views = crsr.fetchone()[0]

        q3c2 = """select count(*) as num from log where time >=
                  '{}' and time <= '{}' and status = '404 NOT FOUND';""".format(q3c_start, q3c_end)
        crsr.execute(q3c2)
        daily_errors = crsr.fetchone()[0]

        err_prcnt = daily_errors / daily_views
        if err_prcnt > 0.01:
            if title_print:
                print('{:>10} -- Of total daily page views:'.format('Date:'))
                title_print = False
            print('{} -- {:.3}% errors'.format(current, (100 * err_prcnt)))

        current += datetime.timedelta(1)
        if current > end:
            break

    dbconn.close()

# Call main and put all logic there per best practices.
if __name__ == '__main__':
    main(sys.argv[1:])

