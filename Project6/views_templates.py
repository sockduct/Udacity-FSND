#!/usr/bin/env python
# -*- coding: ascii -*-
###################################################################################################
#
# Python version(s) used/tested:
# * Python 2.7.12-32 on Ubuntu 16.04.2 LTS
# * Python 2.7.13-32 on Windows 7
# * Python 3.5.2-32  on Ubuntu 16.04.2 LTS
# * Python 3.6.1-32  on Windows 7
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
'''<module/program description> - triple quotes should end on this line if
   on liner...'''

# Future Imports - Must be first, provides Python 2/3 interoperability
from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
from __future__ import division             # 3/2 == 1.5, 3//2 == 1
from __future__ import absolute_import      # prevent implicit relative imports in v2.x
from __future__ import unicode_literals     # all string literals treated as unicode strings

# Imports
from flask import Flask, jsonify, request, url_for, abort, g, render_template, make_response
from flask_httpauth import HTTPBasicAuth
from functools import update_wrapper
import json
from models import Base, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
from pprint import pprint
import ratelimit
import requests
# SQLAlchemy extension to map classes to database tables
from sqlalchemy.ext.declarative import declarative_base
# SQLAlchemy database handle to interact with underlying database
from sqlalchemy.orm import sessionmaker
# x
from sqlalchemy.orm import relationship
# SQLAlchemy module to connect to underlying database
from sqlalchemy import create_engine
import time

# Globals
# Note:  Consider using function/class/method default parameters instead
#        of global constants where it makes sense
# SQLAlchemy setup - create an instance of a connection to the underlying
# database
# Use SQLite:
# DB_PATH = os.path.join(os.path.dirname(__file__), 'catalog.db')
# engine = create_engine('sqlite:///' + DB_PATH)
# Use PostgreSQL, with user catalog:
engine = create_engine('postgresql+psycopg2://catalog:NEKpPllvkcVEP4W9QzyIgDbKH15NM1I96BclRWG5@/catalog')
# Not sure what this does or if it's needed
Base.metadata.bind = engine
# Create ORM handle to underlying database
DBSession = sessionmaker(bind=engine)
# Used to interact with underlying database
session = DBSession()
#
# Flask setup
app = Flask(__name__)
auth = HTTPBasicAuth()
#
# OAuth setup
OAUTH_CLIENT_FILE = 'client_secret_google.json'
OAUTH_CLIENT_FILE_PATH = os.path.join(os.path.dirname(__file__), OAUTH_CLIENT_FILE)
CLIENT_ID = json.loads(open(OAUTH_CLIENT_FILE_PATH).read())['web']['client_id']


# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>att<dot>com'
__date__ = 'July 28, 2017'
__version__ = '0.0.1'


# Integrate these:
@auth.verify_password
def verify_password(username, password):
    user = session.query(User).filter_by(username=username).first()
    # Don't want to notify agent if username not found or password verification
    # failed - this would constitute a security vulnerability
    if not user or not user.verify_password(password):
        return False
    else:
        g.user = user
        return True
#
# Another version:
@auth.verify_password
def verify_password(username_or_token, password):
    #Try to see if it's a token first
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True
#
# Don't like this approach where token is in username, what about using separate
# header like GitHub does?
@auth.verify_password
def verify_password(username_or_token, password):
    # First check if its a token
    # Debugging
    print('Received:  {}:{}'.format(username_or_token, password))
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        # Debugging
        print('Validated by token')
        user = session.query(User).filter_by(id=user_id).one()
    else:
        # Debugging
        print('Trying to validate by username/password...')
        user = session.query(User).filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            # Debugging
            print('Failed to validate auth credentials')
            return False

        # Debugging
        print('Validated by username/password')

    # Successful authentication
    g.user = user
    return True


@app.route('/clientOAuth')
def start():
    return render_template('clientOAuth.html')


@app.route('/oauth/<provider>', methods = ['POST'])
def login(provider):
    # print('Request:  {}'.format(request))
    # print('Request introspection:')
    # pprint(request.__dict__)
    # print('-=-' * 25)
    #STEP 1 - Parse the auth code
    # Use this way if running seafood_test.py script
    ## auth_code = request.json.get('auth_code')
    # Use this way if coming from browser
    auth_code = request.data
    print "Step 1 - Complete, received auth code %s" % auth_code
    # print('-=-' * 25)
    if provider == 'google':
        #STEP 2 - Exchange for a token
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets(OAUTH_CLIENT_FILE, scope='',
                                                 redirect_uri='postmessage')
            ## oauth_flow = flow_from_clientsecrets(OAUTH_CLIENT_FILE, scope='')
            ## oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        # # Verify that the access token is used for the intended user.
        # gplus_id = credentials.id_token['sub']
        # if result['user_id'] != gplus_id:
        #     response = make_response(json.dumps("Token's user ID doesn't match given user ID."),
        #                              401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response

        # # Verify that the access token is valid for this app.
        # if result['issued_to'] != CLIENT_ID:
        #     response = make_response(json.dumps("Token's client ID does not match app's."), 401)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response

        # stored_credentials = login_session.get('credentials')
        # stored_gplus_id = login_session.get('gplus_id')
        # if stored_credentials is not None and gplus_id == stored_gplus_id:
        #     response = make_response(json.dumps('Current user is already connected.'), 200)
        #     response.headers['Content-Type'] = 'application/json'
        #     return response
        print "Step 2 Complete! Access Token : %s " % credentials.access_token

        #STEP 3 - Find User or make a new one

        #Get user info
        h = httplib2.Http()
        userinfo_url =  "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        name = data['name']
        picture = data['picture']
        email = data['email']

        print('Received:\nName:  {}\nPicture:  {}\nEmail:  {}\n'.format(name, picture, email))
        #see if user exists, if it doesn't make a new one
        user = session.query(User).filter_by(email=email).first()
        if not user:
            print('Creating database entry for user...')
            user = User(username = name, picture = picture, email = email)
            session.add(user)
            session.commit()
        else:
            print('User already in database')

        #STEP 4 - Make token
        token = user.generate_auth_token(600)

        #STEP 5 - Send back token to the client
        print('Generated auth token:  {}'.format(token))
        return jsonify({'token': token.decode('ascii')})

        #return jsonify({'token': token.decode('ascii'), 'duration': 600})
    else:
        return 'Unrecoginized Provider'


# /token route to get a token for a user with login credentials
@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    # token.decode(<str>) converts the ASCII "byte-string" to Unicode
    # Believe Python 2.x only but not sure
    return jsonify({'token': token.decode('ascii')})


#ADD a /users route here
@app.route('/users', methods=['POST'])
def registerUser():
    try:
        username = request.json.get('username', '')
        password = request.json.get('password', '')
    except AttributeError as err:
        username = password = None
    if not username or not password:
        print('Missing required parameters (username, password).')
        abort(400)

    user = session.query(User).filter_by(username=username).first()
    if user:
        print('User already exists.')
        return (jsonify({'message': 'User already exists.'}), 200,
                {'Location': url_for('get_user', id=user.id, _external=True)})

    user = User(username=username)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return (jsonify({'username': user.username}), 201, {'Location':
            url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    else:
        return jsonify({'username': user.username})


@app.route('/resource')
@auth.login_required
def get_resource():
    return jsonify({ 'data': 'Hello, %s!' % g.user.username })


@app.route('/bagels', methods = ['GET','POST'])
#protect this route with a required login
@auth.login_required
def showAllBagels():
    if request.method == 'GET':
        print('Hello {}!'.format(g.user.username))
        bagels = session.query(Bagel).all()
        return jsonify(bagels=[bagel.serialize for bagel in bagels])
    elif request.method == 'POST':
        name = request.json.get('name')
        description = request.json.get('description')
        picture = request.json.get('picture')
        price = request.json.get('price')
        newBagel = Bagel(name=name, description=description, picture=picture, price=price)
        session.add(newBagel)
        session.commit()
        return jsonify(newBagel.serialize)


@app.route('/rate-limited')
@ratelimit(limit=300, per=30 * 1)  # Limit to 300 requests per 30 seconds
def index():
    return jsonify({'response':'This is a rate limited response'})


@app.route('/products', methods=['GET', 'POST'])
@auth.login_required
def showAllProducts():
    print('Request:  {}'.format(request))
    if request.method == 'GET':
        products = session.query(Product).all()
        return jsonify(products = [p.serialize for p in products])
    if request.method == 'POST':
        name = request.json.get('name')
        category = request.json.get('category')
        price = request.json.get('price')
        newItem = Product(name=name, category=category, price=price)
        session.add(newItem)
        session.commit()
        return jsonify(newItem.serialize)


@app.route('/products/<category>')
@auth.login_required
def showCategoriedProducts(category):
    if category == 'fruit':
        fruit_items = session.query(Product).filter_by(category = 'fruit').all()
        return jsonify(fruit_products = [f.serialize for f in fruit_items])
    if category == 'legume':
        legume_items = session.query(Product).filter_by(category = 'legume').all()
        return jsonify(legume_products = [l.serialize for l in legume_items])
    if category == 'vegetable':
        vegetable_items = session.query(Product).filter_by(category = 'vegetable').all()
        return jsonify(produce_products = [p.serialize for p in produce_items])


@app.route('/catalog')
@ratelimit.ratelimit(limit=60, per=60 * 1)  # Limit to 300 requests per 30 seconds
def getCatalog():
    items = session.query(Item).all()

    #Populate an empty database
    if items == []:
        item1 = Item(name="Pineapple", price="$2.50",
                     picture=("https://upload.wikimedia.org/wikipedia/commons/c/"
                              "cb/Pineapple_and_cross_section.jpg"),
                     description="Organically Grown in Hawai'i")
        session.add(item1)
        item2 = Item(name="Carrots", price = "$1.99",
                     picture=("http://media.mercola.com/assets/images/food-facts/"
                              "carrot-fb.jpg"), description="High in Vitamin A")
        session.add(item2)
        item3 = Item(name="Aluminum Foil", price="$3.50", picture=(
                     "http://images.wisegeek.com/aluminum-foil.jpg"), description=
                     "300 feet long")
        session.add(item3)
        item4 = Item(name="Eggs", price="$2.00", picture=(
                     "http://whatsyourdeal.com/grocery-coupons/wp-content/uploads/"
                     "2015/01/eggs.png"), description = "Farm Fresh Organic Eggs")
        session.add(item4)
        item5 = Item(name="Bananas", price="$2.15", picture=
                     "http://dreamatico.com/data_images/banana/banana-3.jpg",
                     description="Fresh, delicious, and full of potassium")
        session.add(item5)
        session.commit()
        items = session.query(Item).all()
    return jsonify(catalog=[i.serialize for i in items])


if __name__ == '__main__':
    #app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits)
    #                                   for x in xrange(32))
    app.secret_key = os.urandom(40)
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
    # Watch out for multi-threaded interaction with your database!!!
    ## app.run(host='0.0.0.0', port=5000, threaded=True)
    ## app.run(host='0.0.0.0', port=5000, processes=3)

###################################################################################################
# Post coding
#
# Only test for Python 3 compatibility:  pylint --py3k <script>.py
# pylint <script>.py
#   Score should be >= 8.0
# Alternatives:
# pep8, flake8
#
# python warning options:
# * -Qwarnall - Believe check for old division usage
# * -t - issue warnings about inconsitent tab usage
# * -3 - warn about Python 3.x incompatibilities
#
# python3 warning options:
# * -b - issue warnings about mixing strings and bytes
#
# Future:
# * Testing - doctest/unittest/pytest/other
# * Logging
#

