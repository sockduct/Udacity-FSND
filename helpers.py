#!/usr/bin/env python
# -*- coding: ascii -*-
###################################################################################################
#
# Python version(s) used/tested:
# * Python 2.7.12-32 on Ubuntu 16.04.2 LTS
# * Python 2.7.13-32 on Windows 7
#
# Notes on Style:
# * PEP 8 followed with maximum line length of 99 characters (allowable
#   per: https://www.python.org/dev/peps/pep-0008/#maximum-line-length)
#   * Per above, comments and docstrings must be wrapped at 72 characters
#   * Interpreting this as just the comment/docstring text and not the
#     leading quotes or '# '
#
#
# Template version used:  0.1.2
#
# -------------------------------------------------------------------------------------------------
#
# Issues/PLanned Improvements:
# * TBD
#
'''Helper functions used by views.py.'''

# Future Imports - Must be first, provides Python 2/3 interoperability
from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
from __future__ import division             # 3/2 == 1.5, 3//2 == 1
from __future__ import absolute_import      # prevent implicit relative imports in v2.x
from __future__ import unicode_literals     # all string literals treated as unicode strings

# Imports
import os
import re
# My SQLAlchemy/database table classes
from models import Category, Item, User
# SQLAlchemy database handle to interact with underlying database
from sqlalchemy.orm import sessionmaker
# SQLAlchemy module to connect to underlying database
from sqlalchemy import create_engine
# Handle query error for no matching row found
from sqlalchemy.orm.exc import NoResultFound


# Globals
# Note:  Consider using function/class/method default parameters instead
#        of global constants where it makes sense
#
# SQLAlchemy setup - create an instance of a connection to the underlying database
# Use SQLite:
# DB_PATH = os.path.join(os.path.dirname(__file__), 'catalog.db')
# engine = create_engine('sqlite:///' + DB_PATH)
# Use PostgreSQL, with user catalog:
engine = create_engine('postgresql+psycopg2://catalog:NEKpPllvkcVEP4W9QzyIgDbKH15NM1I96BclRWG5@/catalog')
# Create ORM handle to underlying database
DBSession = sessionmaker(bind=engine)
# Used to interact with underlying database
session = DBSession()
#
# Valid username and password formats
VLD_USERNAME = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
VLD_PASSWORD = re.compile(r'^.{10,40}$')
# Instructor states that in his experience (as lead engineer at Reddit) this
# is good enough.  If the email isn't valid, the email program/tool will
# catch it.  Definitely some wisdom to his KISS thoughts.
VLD_EMAIL = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>att<dot>com'
__date__ = 'July 28, 2017'
__version__ = '0.0.1'


###################################################################################################
# Helper Functions
###################################################################################################
def authed_user(uid):
    user = None
    if uid:
        try:
            user = session.query(User).filter_by(uid=uid).one()
            user = user.serialize
        except NoResultFound as e:
            pass

    return user


def get_user_byid(uid):
    user = None
    if uid:
        try:
            user = session.query(User).filter_by(uid=uid).one()
        except NoResultFound:
            pass

    return user


def check_user_info(params):
    if not VLD_USERNAME.match(params['username']):
        params['username_error'] = ('Invalid username - Must be from 3-20 characters'
                                    ' consisting of a-z, A-Z, 0-9, _, -')
        params['have_error'] = True

    # If this user already exists and there isn't another error
    try:
        user = session.query(User).filter_by(name=params['username']).one()
    except NoResultFound as e:
        user = None
    if params.get('user_unique_chk') and user and not params['have_error']:
        params['username_error'] = ('Username unavailable - already in use, please '
                                    'choose another username')
        params['have_error'] = True

    if not VLD_PASSWORD.match(params['password']):
        params['password_error'] = 'Invalid password - Must be from 10-40 characters long'
        params['have_error'] = True

    if params.get('verify') and not params['password'] == params['verify']:
        params['verify_error'] = "Passwords don't match"
        params['have_error'] = True

    if params.get('email') and not valid_email(params['email']):
        params['email_error'] = ('Invalid E-mail address - Must be name@domain.domain'
                                 ' (e.g., george@yahoo.com)')
        params['have_error'] = True


def valid_email(email):
    # Email optional - only validate if submitted
    if email is None:
        print('no email address included (None)')
        return True
    elif email == '':
        print("no email address included ('')")
        return True
    else:
        return VLD_EMAIL.match(email)


def valid_json(content_type):
    # Valid JSON Content-Type
    return bool(content_type and content_type.lower() == 'application/json')


def validate_category(category_name):
    # Input validation for category
    if category_name:
        try:
            category = session.query(Category).filter_by(name=category_name).one()
        except NoResultFound as e:
            category = None
        # Category doesn't exist within database - must use existing category name
        if not category:
            return False, 'invalid'
        # All good - category_name is valid
        else:
            return True, None
    # Must specify category name
    else:
        return False, 'missing'


def validate_input(item_name, item_description, category_name):
    # Input validation for item
    valid = True
    error = {}

    status, result = validate_item(item_name, item_description, category_name)
    if not status:
        valid = False
        error['title_problem'] = result
        if result == 'nonunique':
            error['title_error'] = ('Error:  "{}" is already in use within the catalog!  '
                                    'Please choose a different name.'.format(item_name))
        elif result == 'missing':
            error['title_error'] = 'Error:  Must specify a name for the item!'

    # Input validation for category
    status, result = validate_category(category_name)
    if not status:
        valid = False
        if result == 'invalid':
            error['catalog_error'] = 'Error:  Must choose an existing catalog category!'
        elif result == 'missing':
            error['catalog_error'] = 'Error:  Must choose a catalog category!'

    return valid, error


def validate_item(item_name, item_description, category_name):
    # Input validation for item
    if item_name:
        try:
            item = session.query(Item).filter_by(name=item_name).one()
        except NoResultFound as e:
            item = None
        # An Item with the name specified already exists in the database - must use a
        # different name
        if item:
            return False, 'nonunique'
        # All good - item_name is unique!
        else:
            return True, None
    # Must specify item name
    else:
        return False, 'missing'

