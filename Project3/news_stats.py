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
# Issues/Planned Improvements:
# * None yet...
#
'''Project 3 - Log Analysis, Analyze fictitious news site to answer statistics questions'''

# Imports
# Python 2.x compatibility:
#from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
#from __future__ import division             # 3/2 == 1.5, 3//2 == 1
#from __future__ import absolute_import      # prevent implicit relative imports in v2.x
#from __future__ import unicode_literals     # all string literals treated as unicode strings
from collections import namedtuple
import psycopg2
import sys

# Globals
# Note:  Consider using function/class/method default parameters instead of global constants where
# it makes sense
DB_NAME = 'news'

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james.r.small@oatt.com'
__date__ = 'June 20, 2017'
__version__ = '0.0.2'

# Data Types:
# Note - quote indicates column data which should be quoted, currently only allows a single
#        column of data to be quoted; value is a number representing the actual column number
#        e.g., Column 1 = 1, Column 2 = 2, ... - but note, Column 1 != 0!!!  Need to do it this
#        way so that can do boolean test - if rec.quote then ..., this won't work if Column 1 = 0
rec = namedtuple('rec', ['count', 'quote', 'headers', 'hlen'])


def fetch_query(query, db_name=DB_NAME):
    '''Query database using passed parameter, fetch and return reference to results.
       Database is opened only to complete this transaction and closed upon function exit.
    '''
    try:
        dbconn = psycopg2.connect('dbname={}'.format(db_name))
        cursor = dbconn.cursor()
        # If it's a tuple, it's a query with a value parameter, unpack it:
        if isinstance(query, tuple):
            cursor.execute(*query)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        dbconn.close()

        return results
    except psycopg2.Error as e:
        print('Error - Unable to connect to the database ({}):\n{}\n'.format(db_name, e))
        sys.exit(1)

def print_top_articles(number=None):
    '''Fetch top <number> articles from database and print results'''
    if number:
        query = ('''select articles.title, count(*) as num
                        from articles, log
                        where articles.slug = regexp_replace(log.path, '^.*/', '')
                        group by articles.title
                        order by num
                        desc limit (%s);''', (number, )
                )
    else:
        query = '''select articles.title, count(*) as num
                        from articles, log
                        where articles.slug = regexp_replace(log.path, '^.*/', '')
                        group by articles.title
                        order by num desc;'''
    results = fetch_query(query)

    # Formatting
    row_rec = rec(count=2, quote=1, headers=['Article', 'Number of Views'], hlen=[34, 'n7'])
    print_results(results, row_rec)

def print_top_authors(number=None):
    '''Fetch top <number> authors from database and print results'''
    if number:
        query = ("""select authors.name, count(*) as num
                        from authors, articles, log
                        where authors.id = articles.author and
                        articles.slug = regexp_replace(log.path, '^.*/', '')
                        group by authors.name
                        order by num desc
                        limit (%s);""", (number, )
                )
    else:
        query = """select authors.name, count(*) as num
                        from authors, articles, log
                        where authors.id = articles.author and
                        articles.slug = regexp_replace(log.path, '^.*/', '')
                        group by authors.name
                        order by num desc;"""
    results = fetch_query(query)

    # Formatting
    row_rec = rec(count=2, quote=None, headers=['Author', "Views of Author's Article(s)"],
                  hlen=[22, 'n7'])
    print_results(results, row_rec)

def print_daily_errors(threshold=None):
    '''Fetch daily view statistics and print days with error percentage > <threshold>.
       Passed percentage will be converted into decimal.  e.g., 1 --> 0.01
    '''

    if threshold:
        # Targeted at Python 3.x, but added .0 for Python 2.x compatibility
        threshold /= 100.0
        query = ("""with daily_reqs as (
                        select date(time), count(*) as num_recs from log group by date(time)
                    ),
                    daily_errs as (
                        select date(time), count(*) as num_errs from (
                            select * from log where status = '404 NOT FOUND') error_logs
                            group by date(time) order by date
                        )
                    select date, err_prcnt from (
                        select daily_reqs.date, daily_reqs.num_recs, daily_errs.num_errs,
                            cast(daily_errs.num_errs as float) / daily_reqs.num_recs as err_prcnt
                                from daily_reqs, daily_errs
                                where daily_reqs.date = daily_errs.date
                        ) req_err_tbl where err_prcnt > (%s);""", (threshold, )
                )
    else:
        ''' The following query produces a table that groups daily views, daily errors and
            calculates the daily error percentage - this is used to determine which days have
            a high percentage of errors:
        '''
        query = '''with daily_reqs as (
                        select date(time), count(*) as num_recs from log group by date(time)
                    ),
                    daily_errs as (
                        select date(time), count(*) as num_errs from (
                            select * from log where status = '404 NOT FOUND') error_logs
                            group by date(time) order by date
                        )
                    select daily_reqs.date, daily_reqs.num_recs, daily_errs.num_errs,
                            cast(daily_errs.num_errs as float) / daily_reqs.num_recs as err_prcnt
                                from daily_reqs, daily_errs
                                where daily_reqs.date = daily_errs.date;'''
    results = fetch_query(query)

    # Formatting
    if threshold:
        row_rec = rec(count=2, quote=None, headers=['Date', 'Error % of total daily page views'],
                      hlen=['d12', 'f32'])
    else:
        row_rec = rec(count=4, quote=None, headers=['Date', 'Daily total page views',
                      'Daily total view errors', 'Error % of total daily page views'],
                      hlen=['d12', 'n22', 'n23', 'f32'])
    print_results(results, row_rec)

def format_col(value):
    '''Format column according to encoded type:
         *    int - simple column width
         * string - encoded meaning depending on first character:
         *   d - format as date:    Month DD, YEAR (field width follows 'd' but assume 12)
                                    12 is length of MMM DD, YEAR - MMM is abbreviated month
         *   n - format as number:  d,ddd,ddd (field width follows 'n')
         *   f - format as float:   ###.## (leading and trailing digits follow 'f' but assume 32)
    '''
    # Default value, only altered for type 'f'
    htrail = 0

    if isinstance(value, int):
        ftype = 's'
        hlen = value
    elif value[0] == 'd':
        ftype = 'd'
        hlen = 12  # Could parse out (int(value[1:])), but for now always 12
    elif value[0] == 'n':
        ftype = 'n'
        hlen = int(value[1:])
    elif value[0] == 'f':
        ftype = 'f'
        hlen = 3  # Could parse out (int(value[1])), but for now always 3
        htrail = 2  # Could parse out (int(value[2])), but for now always 2
    else:
        raise ValueError('Unexpected second header length type "{}".'.format(value[0]))

    return ftype, hlen, htrail

def print_results(results, cfmt=None):
    '''Execute query against database connection and print results'''
    title_print = True
    for row in results:
        if cfmt and cfmt.count >= 2:
            if title_print:
                title_print = False
                total_hlen = 0
                for elmt in range(cfmt.count):
                    # Note - htrail not currently used but left in for potential future
                    #        improvements
                    ftype, hlen, htrail = format_col(cfmt.hlen[elmt])

                    if cfmt.quote and elmt == (cfmt.quote - 1):
                        hlen += 2

                    # Not last header
                    if elmt + 1 < cfmt.count:

                        # Check if hlen is smaller than header column with ':' - if yes than need
                        # to increase width of hlen by one:
                        if hlen < (len(cfmt.headers[elmt]) + 1):
                            hlen += 1

                        total_hlen += hlen
                        header = cfmt.headers[elmt] + ':'
                        print('{:>{width}} -- '.format(header, width=hlen), end='')
                    # Last header
                    else:
                        total_hlen += len(cfmt.headers[elmt]) + 1
                        print('{}:'.format(cfmt.headers[elmt]))
                # Title/Data separator
                # Account for ' -- ' between each column
                total_hlen += (cfmt.count - 1) * 4
                print('=' * total_hlen)

            for elmt in range(cfmt.count):
                ftype, hlen, htrail = format_col(cfmt.hlen[elmt])

                # Record format indicates this element should be quoted
                if cfmt.quote and elmt == (cfmt.quote - 1):
                    hlen += 2
                    col = '"' + row[elmt] + '"'
                # Unquoted element
                else:
                    col = row[elmt]

                # Check if column data is smaller than header with ':' - if yes than need to
                # increase width of data column by one:
                if hlen < (len(cfmt.headers[elmt]) + 1):
                    hlen += 1

                if ftype == 's':
                    print('{:>{width}}'.format(col, width=hlen), end='')
                elif ftype == 'n':
                    print('{:>{width},}'.format(col, width=hlen), end='')
                elif ftype == 'd':
                    print('{:%b %d, %Y}'.format(col), end='')
                elif ftype == 'f':
                    print('{:>3.2f}'.format((col * 100)), end='')

                # Not last header
                if elmt + 1 < cfmt.count:
                    print(' -- ', end='')
            # Terminate row with newline
            print('')
        else:
            print('row:  {} ({})'.format(row, type(row)))

    # Print an empty line
    print('')

def main(args):
    '''Answer following questions:
        1) What are the most popular three articles of all time?
        2) Who are the most popular article authors of all time?
        3) On which days did more than 1% of requests lead to errors?
    '''
    print_top_articles(3)
    print_top_authors()
    print_daily_errors(1.0)

# Call main and put all logic there per best practices.
if __name__ == '__main__':
    main(sys.argv[1:])

