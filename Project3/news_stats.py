#!/usr/bin/env python3
# -*- coding: ascii -*-
# Default is ascii - explicitly coding, could also consider utf-8,
#                    latin-1, cp1252, ...
###################################################################################################
#
# Python version(s) used/tested:
# * Python 3.5.2-32 on Linux (Ubuntu 16.04.2 LTS)
#
# Template version used:  0.1.1
#
# Notes on Style:
# * PEP 8 followed with maximum line length of 99 characters (allowable
#   per: https://www.python.org/dev/peps/pep-0008/#maximum-line-length)
#   * Per above, comments and docstrings must be wrapped at 72 characters
#   * Interpreting this as just the comment/docstring text and not the
#     leading quotes or '# '
#
# -------------------------------------------------------------------------------------------------
#
# Issues/Planned Improvements:
# * None yet...
#
'''Project 3 - Log Analysis, Analyze fictitious news site to answer
   statistics questions'''

# Imports
# Python 2.x compatibility:
# from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
# from __future__ import division             # 3/2 == 1.5, 3//2 == 1
# from __future__ import absolute_import      # prevent implicit relative imports in v2.x
# from __future__ import unicode_literals     # all string literals treated as unicode strings
from collections import namedtuple
import psycopg2
# Importing sql this way per psycopg2 docs - sql not imported from
# psycopg2
from psycopg2 import sql
import sys

# Globals
# Note:  Consider using function/class/method default parameters instead
#        of global constants where it makes sense
DB_NAME = 'news'

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james.r.small@att.com'
__date__ = 'June 20, 2017'
__version__ = '0.0.4'

# Data Types:
# Note - Formatting record, used to collect all aspects of laying out
#        columns quote indicates column data which should be quoted,
#        currently only allows a single column of data to be quoted;
#        value is a number representing the actual column number, e.g.,
#        Column 1 = 1, Column 2 = 2, ... - but note, Column 1 != 0!!!
#        Need to do it this way so that can do boolean test - if
#        FormatRec.quote then ..., this won't work if Column 1 = 0
FormatRec = namedtuple('FormatRec', ['count', 'quote', 'headers', 'hlen'])


def fetch_query(query, db_name=DB_NAME):
    '''Query database using passed parameter, fetch and return reference to
       results.  Database is opened only to complete this transaction and
       closed upon function exit.
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
        print('Error - Either unable to connect to the database ({}) or exception occurred '
              'running\nquery:\n{}\n'.format(db_name, e))
        sys.exit(1)


def print_top_articles(number=None):
    '''Fetch top <number> articles from database and print results'''
    if not number:
        # In PostgeSQL, using the keyword ALL in the LIMIT clause results in all
        # rows being returned.  In no limit specified as a parameter, default to
        # 'ALL'.
        number = 'all'
        # Note - Adding a SQL keyword to a query requires using psycopg2.sql to
        #        build a "dynamic query"
        dynamic_sql = True
    else:
        # If we're just adding a parameter to a query (limit the number to x rows)
        # we can use the built-in literal support (we don't need to construct a
        # dynamic SQL query)
        dynamic_sql = False

    query = """select articles.title, num
                    from articles, (select path, count(*) as num
                        from log
                        group by path) as log
                    where articles.slug = regexp_replace(log.path, '^.*/', '')
                    order by num desc
                    limit """
    if dynamic_sql:
        query = sql.SQL('{} {};'.format(query, number))
    else:
        query = (query + "(%s);", (number, ))

    results = fetch_query(query)

    # Formatting
    ColFormat = FormatRec(count=2, quote=1, headers=['Article', 'Number of Views'],
                          hlen=[34, 'n6'])
    print_results(results, ColFormat)


def print_top_authors(number=None):
    '''Fetch top <number> authors from database and print results'''
    if not number:
        # Refer to comments in print_top_articles() for number and dynamic_sql
        number = 'all'
        dynamic_sql = True
    else:
        dynamic_sql = False

    query = """select authors.name, sum(num) as total
                    from authors, articles, (select path, count(*) as num
                        from log
                        group by path) as log
                    where authors.id = articles.author and
                    articles.slug = regexp_replace(log.path, '^.*/', '')
                    group by authors.name
                    order by total desc
                    limit """
    if dynamic_sql:
        query = sql.SQL('{} {};'.format(query, number))
    else:
        query = (query + "(%s);", (number, ))

    results = fetch_query(query)

    # Formatting
    ColFormat = FormatRec(count=2, quote=None, headers=['Author', "Views of Author's Article(s)"],
                          hlen=[22, 'n6'])
    print_results(results, ColFormat)


def print_daily_errors(threshold=None):
    '''Fetch daily view statistics and print days with error percentage >
       <threshold>.  Passed percentage will be converted into decimal.
       e.g., 1 --> 0.01
    '''
    if not threshold:
        threshold = 0

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
                    ) req_err_tbl where err_prcnt > (%s);""", (threshold, ))
    results = fetch_query(query)

    # Formatting
    ColFormat = FormatRec(count=2, quote=None, headers=['Date',
                          'Error % of total daily page views'], hlen=['d12', 'f32'])
    print_results(results, ColFormat)


def print_daily_stats():
    '''Fetch daily view statistics and print out all days - total views,
       errors, error percentage for each day.
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
    ColFormat = FormatRec(count=4, quote=None, headers=['Date', 'Daily total page views',
                          'Daily total view errors', 'Error % of total daily page views'],
                          hlen=['d12', 'n22', 'n23', 'f32'])
    print_results(results, ColFormat)


def format_col(value):
    '''Format column according to encoded type:
         *    int - simple column width
         * string - encoded meaning depending on first character:
           * d - format as date:    Month DD, YEAR (field width follows 'd'
                                    but assume 12) 12 is length of MMM DD,
                                    YEAR - MMM is abbreviated month
           * n - format as number:  d,ddd,ddd (field width follows 'n')
           * f - format as float:   ###.## (leading and trailing digits
                                    follow 'f' but assume 32)
    '''
    # Default value, only altered for type 'f', represents number of digits
    # displayed after the decimal point
    hfrac = 0

    if isinstance(value, int):
        # Position type used for formatting, s = string
        postype = 's'
        hlen = value
    elif value[0] == 'd':
        # d = date format type
        postype = 'd'
        hlen = 12  # Could parse out (int(value[1:])), but for now always 12
    elif value[0] == 'n':
        # n = integer number format type
        postype = 'n'
        hlen = int(value[1:])
    elif value[0] == 'f':
        # f = floating point number format type
        postype = 'f'
        hlen = 3  # Could parse out (int(value[1])), but for now always 3
        hfrac = 2  # Could parse out (int(value[2])), but for now always 2
    else:
        raise ValueError('Unexpected second header length type "{}".'.format(value[0]))

    return postype, hlen, hfrac


def print_results(results, ColFormat=None):
    '''Execute query against database connection and print results'''
    title_print = True
    for row in results:
        if ColFormat and ColFormat.count >= 2:
            if title_print:
                title_print = False
                total_hlen = 0
                for element in range(ColFormat.count):
                    # Note - hfrac not currently used but left in for potential
                    #        future improvements
                    postype, hlen, hfrac = format_col(ColFormat.hlen[element])

                    if ColFormat.quote and element == (ColFormat.quote - 1):
                        hlen += 2

                    # Not last header
                    if element + 1 < ColFormat.count:

                        # Check if hlen is smaller than header column with ':' - if
                        # yes than need to increase width of hlen by one:
                        if hlen < (len(ColFormat.headers[element]) + 1):
                            hlen += 1

                        total_hlen += hlen
                        header = ColFormat.headers[element] + ':'
                        print('{:>{width}} -- '.format(header, width=hlen), end='')
                    # Last header
                    else:
                        total_hlen += len(ColFormat.headers[element]) + 1
                        print('{}:'.format(ColFormat.headers[element]))
                # Title/Data separator
                # Account for ' -- ' between each column
                total_hlen += (ColFormat.count - 1) * 4
                print('=' * total_hlen)

            for element in range(ColFormat.count):
                postype, hlen, hfrac = format_col(ColFormat.hlen[element])

                # Record format indicates this element should be quoted
                if ColFormat.quote and element == (ColFormat.quote - 1):
                    hlen += 2
                    col = '"' + row[element] + '"'
                # Unquoted element
                else:
                    col = row[element]

                # Check if column data is smaller than header with ':' - if yes
                # than need to increase width of data column by one:
                if hlen < (len(ColFormat.headers[element]) + 1):
                    hlen += 1

                if postype == 's':
                    print('{:>{width}}'.format(col, width=hlen), end='')
                elif postype == 'n':
                    print('{:>{width},}'.format(col, width=hlen), end='')
                elif postype == 'd':
                    print('{:%b %d, %Y}'.format(col), end='')
                elif postype == 'f':
                    print('{:>3.2f}'.format((col * 100)), end='')

                # Not last header
                if element + 1 < ColFormat.count:
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
    # Optional test run which uses all functions and does alternate
    # parameters to fully test their branches
    if len(args) >= 1 and args[0] == 'test':
        print_top_articles()
        print_top_authors(2)
        print_daily_errors()
        print_daily_stats()
    else:
        print_top_articles(3)
        print_top_authors()
        print_daily_errors(1)


# Call main and put all logic there per best practices.
if __name__ == '__main__':
    main(sys.argv[1:])

