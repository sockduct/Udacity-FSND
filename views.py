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
# * Everything that can have a docstring should!
# * Instead of print statements for debugging use logger (logging)
# * Add auth for browser-based views
# * Add template support for flashing
# * Fix API access to user picture
# * Add API support to upload user picture
# * Consider supporting multiple item upload via API
# * Consider storing and utilizing refresh_tokens (OAuth)
# * Use Google's discovery document (OpenID) instead of hardcoding API endpoints
# * When complete OAuth sequence, check user fields in DB and update if they've changed
# * Leverage OAuth picture/profile - perhaps if click on logged in as <name> show them?
# * Get signin redirects to work with Google OAuth (only works with local logins because
#   OAuth redir done in JavaScript on web page...; idea - use query parameters instead
#   of cookie value as that's accessible from web page/JavaScript
# * For abort(<status_code>) error - create a nice web page to redirect to explaining
#   the error
# * In authorization check, see if user is admin and if yes allow them to do anything
# * Make authed_user into a decorator, also consider same for checking if category_id
#   exists, if item_id exists, if user owns passed entity (e.g., item/category)
# * For SQLAlchemy, instead of try, query, catch, assign None look at one_or_none()
# * Consider creating front end app using React or Angular to leverage API
#
'''Views for my catalog project - supports both browser-based and API-based access'''

# Future Imports - Must be first, provides Python 2/3 interoperability
from __future__ import print_function       # print(<strings>, file=sys.stdout, end='\n')
from __future__ import division             # 3/2 == 1.5, 3//2 == 1
from __future__ import absolute_import      # prevent implicit relative imports in v2.x
from __future__ import unicode_literals     # all string literals treated as unicode strings

# Imports
#
# General
import hashlib
import httplib2
import json
import os
import requests
import sys
#
# Flask:
from flask import (abort, flash, Flask, g, jsonify, make_response, render_template, redirect,
                   request, send_file, session as websession, url_for)
# session -> websession since choose to use session for SQLAlchemy session
from flask_uploads import (configure_uploads, IMAGES, patch_request_class, UploadNotAllowed,
                           UploadSet)
from flask_httpauth import HTTPBasicAuth
#
# Google OAuth 2 Library
from oauth2client.client import (credentials_from_clientsecrets_and_code, FlowExchangeError,
                                 OAuth2Credentials, TokenRevokeError,
                                 UnknownClientSecretsFlowError)
from oauth2client.clientsecrets import InvalidClientSecretsError
#
# SQLAlchemy
# My SQLAlchemy/database table classes
from models import Category, Item, User
# SQLAlchemy database handle to interact with underlying database
from sqlalchemy.orm import sessionmaker
# SQLAlchemy module to connect to underlying database
from sqlalchemy import create_engine
# Handle query error for no matching row found
from sqlalchemy.orm.exc import NoResultFound
#
# Mine
from helpers import (authed_user, check_user_info, get_user_byid, valid_json,
                     validate_category, validate_input)


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
# Flask setup
app = Flask(__name__)
# Uploaded file destination directory
app.config['UPLOADED_PHOTOS_DEST'] = '/vagrant/catalog/static/uploads'
# Limit photo size to 512KB
patch_request_class(app, 512 * 1024)
# Select file set - image files
uploaded_photos = UploadSet('photos', IMAGES)
configure_uploads(app, uploaded_photos)
# Authentication
auth = HTTPBasicAuth()
#
# OAuth 2 Setup
CLIENT_SECRET_FILE = 'client_secret_google.json'
CLIENT_SECRET_FILE_PATH = os.path.join(os.path.dirname(__file__), CLIENT_SECRET_FILE)
OAuth_Client_Info = json.loads(open(CLIENT_SECRET_FILE_PATH).read())['web']
CLIENT_ID = OAuth_Client_Info['client_id']
#
# Default item picture file and storage
DEFAULT_PHOTO_STORE = '/static/uploads/'
DEFAULT_PHOTO = '/static/img/items-generic.jpg'
# Default User Type
USER_TYPE = 'user'
# Load App Secret Key (if it exists)
cfg_file = None
SECRET_KEY = None
try:
    cfg_file = open(os.path.join(os.path.dirname(__file__), 'app_secret.json'))
except IOError as e:
    print('app_secret.json not found ({}) - will generate app secret key...'.format(e))
if cfg_file:
    try:
        SECRET_KEY = json.load(cfg_file)
    except ValueError as e:
        print('Unable to read app secret key from app_secret.json ({}) - will generate it...'
              ''.format(e))
if SECRET_KEY:
    app.secret_key = SECRET_KEY
else:
    # If we have to generate an app secret key then save it - that way if the app
    # is restarted, we'll still use the same secret key.  I believe this is needed
    # so that persistent user cookies ("websession") remain valid.
    # Got this implementation idea from Google docs
    random_state = hashlib.sha256(os.urandom(1024)).hexdigest()
    app.secret_key = random_state
    # Save
    with open(os.path.join(os.path.dirname(__file__), 'app_secret.json'), 'w') as key_file:
        json.dump(random_state, key_file)


# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>att<dot>com'
__date__ = 'July 28, 2017'
__version__ = '0.0.1'


###################################################################################################
# Human/Browser targeted routes/views:
###################################################################################################
@app.route('/')
@app.route('/catalog')
def show_catalog():
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).order_by(Item.name).all()
    item_count = session.query(Item).count()
    user = get_user_byid(websession.get('user_id'))

    return render_template('landing.html', categories=categories, items=items,
                           category_view='all', item_count=item_count, user=user)


@app.route('/catalog/category/<int:cid>')
def show_category(cid):
    categories = session.query(Category).order_by(Category.name).all()
    category_view = session.query(Category).filter_by(cid=cid).one()
    items = session.query(Item).filter_by(category_id=cid).order_by(Item.name).all()
    item_count = session.query(Item).filter_by(category_id=cid).count()

    return render_template('landing.html', categories=categories, items=items,
                           category_view=category_view.name, item_count=item_count)


@app.route('/catalog/item/<int:iid>')
def show_item(iid):
    categories = session.query(Category).order_by(Category.name).all()
    item = session.query(Item).filter_by(iid=iid).one()
    category_view = item.category.name

    return render_template('item.html', categories=categories, item=item,
                           category_view=category_view)


@app.route('/catalog/add/item', methods=['GET', 'POST'])
def add_item():
    user_id = websession.get('user_id')
    if not authed_user(user_id):
        # websession['auth_redir'] = 'add_item'
        return redirect(url_for('signin'))

    if request.method == 'GET':
        categories = session.query(Category).order_by(Category.name).all()

        return render_template('item-cud.html', cud_type='Add', categories=categories,
                               item={'picture': DEFAULT_PHOTO, 'category': {}})
    elif request.method == 'POST':
        # Retrieve form data - use .get to avoid 400 status
        item_name = request.form.get('name')
        item_description = request.form.get('description')
        picture_file = request.files.get('file')
        category_name = request.form.get('category')

        # Input validation
        status, error = validate_input(item_name, item_description, category_name)

        # Deal with picture
        if picture_file:
            try:
                # filename is the path to the image
                filename = DEFAULT_PHOTO_STORE + uploaded_photos.save(picture_file)
                flash('Photo Successfully Uploaded')
            except UploadNotAllowed:
                error['file_error'] = "The picture file upload wasn't allowed."
                filename = None
                status = False

        if not status:
            categories = session.query(Category).order_by(Category.name).all()
            return render_template('item-cud.html', cud_type='Add', categories=categories,
                                   item={'name': item_name, 'description': item_description,
                                         'category': {'name': category_name}},
                                   title_error=error.get('title_error'),
                                   file_error=error.get('file_error'),
                                   category_error=error.get('category_error'))

        # If no picture supplied, use default
        if not picture_file or not filename:
            filename = DEFAULT_PHOTO

        user = session.query(User).filter_by(uid=user_id).one()
        category = session.query(Category).filter_by(name=category_name).one()
        item = Item(name=item_name, picture=filename, description=item_description,
                    category_id=category.cid, user_id=user.uid)
        session.add(item)
        session.commit()
        # Add flashing...
        flash('New Item Created')

        return redirect(url_for('show_item', iid=item.iid))


@app.route('/catalog/edit/item/<int:iid>', methods=['GET', 'POST'])
def edit_item(iid):
    user_id = websession.get('user_id')
    if not authed_user(user_id):
        # websession['auth_redir'] = 'edit_item'
        return redirect(url_for('signin'))

    # This could return none - use one_or_none instead!
    item = session.query(Item).filter_by(iid=iid).one()

    # Authorization Check
    if item.user_id != user_id:
        print('item.user_id ({}) != user_id ({})'.format(item.user_id, user_id))
        abort(403)

    if request.method == 'GET':
        categories = session.query(Category).order_by(Category.name).all()

        return render_template('item-cud.html', cud_type='Edit', categories=categories,
                               item=item)
    elif request.method == 'POST':
        # Retrieve form data - use .get to avoid 400 status
        item_name = request.form.get('name')
        item_description = request.form.get('description')
        picture_file = request.files.get('file')
        category_name = request.form.get('category')

        # Input validation
        status, error = validate_input(item_name, item_description, category_name)

        # Deal with picture
        if picture_file:
            try:
                # filename is the path to the image
                filename = DEFAULT_PHOTO_STORE + uploaded_photos.save(picture_file)
                flash('Photo Successfully Uploaded')
            except UploadNotAllowed:
                error['file_error'] = "The picture file upload wasn't allowed."
                filename = None
                status = False

        if not status:
            # Check if only problem is non-unique name/title (OK since updating):
            valid_set = {'title_error', 'title_problem'}
            # Where overwriting existing item, make sure item.name (looked up from passed
            # iid) matches item_name or we'll get a database error!
            if not (error.get('title_problem') == 'nonunique' and item.name == item_name
                    and valid_set == set(error)):
                categories = session.query(Category).order_by(Category.name).all()
                return render_template('item-cud.html', cud_type='Edit', categories=categories,
                                       item={'name': item_name, 'description': item_description,
                                             'category': {'name': category_name}},
                                       title_error=error.get('title_error'),
                                       file_error=error.get('file_error'),
                                       category_error=error.get('category_error'))

        category = session.query(Category).filter_by(name=category_name).one()

        # Only change picture if new one supplied
        if not picture_file or not filename:
            filename = item.picture

        # Update
        item.name = item_name
        item.picture = filename
        item.description = item_description
        item.category_id = category.cid
        item.user_id = user_id
        session.add(item)
        session.commit()
        # Add flashing...
        flash('Item Updated')

        return redirect(url_for('show_item', iid=item.iid))


@app.route('/catalog/delete/item/<int:iid>', methods=['GET', 'POST'])
def delete_item(iid):
    user_id = websession.get('user_id')
    if not authed_user(user_id):
        # websession['auth_redir'] = 'delete_item'
        return redirect(url_for('signin'))

    item = session.query(Item).filter_by(iid=iid).one()

    # Authorization Check
    if item.user_id != user_id:
        print('item.user_id ({}) != user_id ({})'.format(item.user_id, user_id))
        abort(403)

    if request.method == 'GET':
        categories = session.query(Category).order_by(Category.name).all()

        return render_template('item-cud.html', cud_type='Delete', categories=categories,
                               item=item, read_only=True)
    elif request.method == 'POST':
        session.delete(item)
        session.commit()
        # Add flashing...
        flash('Item Deleted')

        return redirect(url_for('show_catalog'))


###################################################################################################
# Machine/API targeted routes/views (CRUD):
###################################################################################################
# Create views
@app.route('/api/v0/catalog/create/category', methods=['POST'])
@auth.login_required
def create_category_api():
    # Consider allowing creation of one or multiple categories through a single POST
    # For now allow creation of one category at a time
    # Content:  {'category': 'new-category'}
    if valid_json(request.headers.get('content-type')):
        data = request.get_json()
        new_category = data.get('category')
    else:
        return jsonify(error="Unsupported content-type - expecting application/json."), 400

    if new_category:
        status, result = validate_category(new_category)
        # False and 'invalid' means category not in database - this is what we want
        if not status and result == 'invalid':
            user = g.user
            category = Category(name=new_category, user_id=user['uid'])
            session.add(category)
            session.commit()

            return jsonify(category=category.serialize), 201
        # Category already exists
        else:
            return jsonify(error="Category name already exists."), 409
    # Didn't receive valid data
    else:
        return jsonify(error="Couldn't find category name in JSON data."), 400


# Need separate API to upload picture and link to item...
@app.route('/api/v0/catalog/create/item', methods=['POST'])
@auth.login_required
def create_item_api():
    # Allow creation of one or multiple items through a single POST
    # Content:
    # * Single: {'item': {'name': 'item-name', 'description': 'item-description',
    #                     'category_name': 'item-category'}}
    # * Multiple: {'items': [{'name': 'item-name', 'description': 'item-description',
    #                         'category_name': 'item-category'},
    #                        {<next-item...>}]}
    if valid_json(request.headers.get('content-type')):
        data = request.get_json()
    else:
        return jsonify(error="Unsupported content-type - expecting application/json."), 400

    # Determine if single or multiple items
    new_item = data.get('item')
    new_items = data.get('items')

    # Single item?
    if new_item:
        name = new_item.get('name')
        description = new_item.get('description')
        category_name = new_item.get('category_name')

        status, error = validate_input(name, description, category_name)
        # True means item not in database - this is what we want
        if status:
            user = g.user
            category = session.query(Category).filter_by(name=category_name).one()
            filename = DEFAULT_PHOTO

            item = Item(name=name, description=description, picture=filename,
                        category_id=category.cid, user_id=user['uid'])
            session.add(item)
            session.commit()

            return jsonify(item=item.serialize), 201
        # Problems
        else:
            return jsonify(error=error), 406
    # Multiple items?
    elif new_items:
        # Parse through each item, validate, and add if good
        # Need to keep track of successes and failures and report on at the end
        # This last part could be tricky...

        return jsonify(error='Not implemented...')
    # Didn't receive valid data
    else:
        return jsonify(error="Couldn't find item/items in JSON data."), 400


# Read views
@app.route('/api/v0/catalog')
def show_catalog_api():
    categories = session.query(Category).order_by(Category.name).all()
    items = session.query(Item).order_by(Item.name).all()

    return jsonify(categories=[i.serialize for i in categories],
                   items=[i.serialize for i in items])


@app.route('/api/v0/catalog/category/<int:cid>')
@app.route('/api/v0/catalog/read/category/<int:cid>')
def read_category_api(cid):
    category = session.query(Category).filter_by(cid=cid).one()

    # Could also return the items belonging with the category but decided against for API
    # items = session.query(Item).filter_by(category_id=cid).order_by(Item.name).all()
    # return jsonify(category=category.serialize, items=[i.serialize for i in items])

    return jsonify(category=category.serialize)


@app.route('/api/v0/catalog/item/<int:iid>')
@app.route('/api/v0/catalog/read/item/<int:iid>')
def read_item_api(iid):
    item = session.query(Item).filter_by(iid=iid).one()

    return jsonify(item=item.serialize)


# Doesn't seem to work...
@app.route('/api/v0/catalog/item/<int:iid>/picture')
@app.route('/api/v0/catalog/read/item/<int:iid>/picture')
def read_item_picture_api(iid):
    item = session.query(Item).filter_by(iid=iid).one()

    return send_file(item.picture)


# Update views
@app.route('/api/v0/catalog/update/category/<int:cid>', methods=['POST'])
@auth.login_required
def update_category_api(cid):
    # Content:  {'category': 'updated-category-name'}
    if valid_json(request.headers.get('content-type')):
        data = request.get_json()
        update_category = data.get('category')
    else:
        return jsonify(error="Unsupported content-type - expecting application/json."), 400

    if update_category:
        try:
            category = session.query(Category).filter_by(cid=cid).one()
        except NoResultFound as e:
            category = None

        if category:
            if g.user['uid'] != category.user_id:
                return jsonify(error='Not authorized'), 403

            category.name = update_category
            session.add(category)
            session.commit()

            return jsonify(category=category.serialize)
        # Category doesn't exist
        else:
            return jsonify(error="Category ID doesn't exist."), 422
    # Didn't receive valid data
    else:
        return jsonify(error="Couldn't find category name in JSON data."), 400


@app.route('/api/v0/catalog/update/item/<int:iid>', methods=['POST'])
@auth.login_required
def update_item_api(iid):
    # Content:  {'item': {'name': 'new--name', 'description': 'new-description',
    #                     'category_name': 'new-category'}}
    # Note - cannot change picture through this view
    if valid_json(request.headers.get('content-type')):
        data = request.get_json()
        update_item = data.get('item')
    else:
        return jsonify(error="Unsupported content-type - expecting application/json."), 400

    if update_item:
        try:
            item = session.query(Item).filter_by(iid=iid).one()
        except NoResultFound as e:
            item = None

        if item:
            if g.user['uid'] != item.user_id:
                return jsonify(error='Not authorized'), 403

            name = update_item.get('name')
            description = update_item.get('description')
            category_name = update_item.get('category_name')

            status, error = validate_input(name, description, category_name)
            if not status:
                # Check if only problem is non-unique name/title (OK since updating):
                valid_set = {'title_error', 'title_problem'}
                # Where overwriting existing item, make sure item.name (looked up from passed
                # iid) matches item_name or we'll get a database error!
                if not (error.get('title_problem') == 'nonunique' and item.name == name
                        and valid_set == set(error)):
                    return jsonify(error=error), 406

            category = session.query(Category).filter_by(name=category_name).one()

            # Update
            item.name = name
            item.description = description
            item.category_id = category.cid
            session.add(item)
            session.commit()

            return jsonify(item=item.serialize)
        # Category doesn't exist
        else:
            return jsonify(error="Category ID doesn't exist."), 422
    # Didn't receive valid data
    else:
        return jsonify(error="Couldn't find item in JSON data."), 400


@app.route('/api/v0/catalog/update/item/<int:iid>/picture', methods=['POST'])
@auth.login_required
def update_item_picture_api(iid):
    # Accept uploaded image and update item.picture file location pointer
    return jsonify(error='Not implemented...')


# Delete views
@app.route('/api/v0/catalog/delete/category/<int:cid>', methods=['POST'])
@auth.login_required
def delete_category_api(cid):
    try:
        category = session.query(Category).filter_by(cid=cid).one()
    except NoResultFound as e:
        category = None

    if category:
        if g.user['uid'] != category.user_id:
            return jsonify(error='Not authorized'), 403

        session.delete(category)
        session.commit()

        return jsonify(success="Category deleted.")
    # Category doesn't exist
    else:
        return jsonify(error="Category ID doesn't exist."), 422


@app.route('/api/v0/catalog/delete/item/<int:iid>', methods=['POST'])
@auth.login_required
def delete_item_api(iid):
    try:
        item = session.query(Item).filter_by(iid=iid).one()
    except NoResultFound as e:
        item = None

    if item:
        if g.user['uid'] != item.user_id:
            return jsonify(error='Not authorized'), 403

        session.delete(item)
        session.commit()

        return jsonify(success="Item deleted.")
    # Category doesn't exist
    else:
        return jsonify(error="Item ID doesn't exist."), 422


###################################################################################################
# Authentication routes/views (Human & Machine):
###################################################################################################
# Note - this authentication type is only intended for API access
# In other words - it's not targeted for browsers but for programs
@auth.verify_password
def verify_password(username_or_token, password):
    # First try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # Try to authenticate with username/password
        try:
            user = session.query(User).filter_by(name=username_or_token).one()
        except NoResultFound as e:
            user = None
        if not user or not user.verify_password(password):
            return False
        # verify_auth_token returns serialized user format so do the same for this path
        user = user.serialize
    # User g because this particular request is now authenticated
    g.user = user
    return True


@app.route('/api/v0/token')
@auth.login_required
def get_auth_token():
    user = session.query(User).filter_by(uid=g.user['uid']).one()
    token = user.gen_auth_token()

    return jsonify({'token': token.decode('ascii')})


@app.route('/api/v0/test')
@auth.login_required
def get_resource():
    return jsonify({'data': g.user})


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        # Generate state used for Anti-CSRF and recommended in OAuth2 specs
        # Got this implementation idea from Google docs
        random_state = hashlib.sha256(os.urandom(1024)).hexdigest()

        # Store in websession
        websession['state'] = random_state

        # Parameters for signin page:
        # openid - we want authentication too and basic info about user
        # profile - Google user profile info
        # email - Google user's email address
        scope = 'openid profile email'

        return render_template('signin.html', state=random_state, scope=scope,
                               client_id=CLIENT_ID)
    elif request.method == 'POST':
        # Not needed in flask
        # host = request.url_root.split('/')[2]
        username = request.form.get('username')
        password = request.form.get('password')
        auth_cookie = request.form.get('auth_cookie')
        state = request.form.get('state')

        # Validate state - does state query parameter match one stored in
        # session cookie?
        if state != websession['state']:
            print('Debug/state check failed!')
            response = make_response(json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        params = dict(username=username, password=password, auth_cookie=auth_cookie,
                      username_error='', password_error='', auth_error='', have_error=False)

        check_user_info(params)

        if params['have_error']:
            print('/signin - authentication error')
            params['password'] = ''
            return render_template('signin.html', **params)
        # Acceptable credentials - check if valid
        else:
            print('/signin - attempting login...')

            try:
                user = session.query(User).filter_by(name=username).one()
            except NoResultFound as e:
                item = None
            # Valid username/password?
            if user and user.verify_password(password):
                # Send back a session cookie or cookie with a 30 day TTL
                # websession['username'] = user.serialize
                # Just store user ID versus serialized user object
                websession['user_id'] = user.uid
                websession['provider'] = 'Local'
                # Note - default lifetime is actually 31 days...
                websession.permanent = True if auth_cookie else False

                # auth_redir = websession.pop('auth_redir', None)
                # if auth_redir:
                #    return redirect(url_for(auth_redir))
                # else:
                return redirect(url_for('show_catalog'))
            # Invalid username and/or password
            else:
                params['password'] = ''
                params['auth_error'] = 'Invalid username and/or password'

                return render_template('signin.html', **params)


@app.route('/signout')
def signout():
    disconnect()

    return redirect(url_for('show_catalog'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        # Not needed in flask
        # host = request.url_root.split('/')[2]
        username = request.form.get('username')
        password = request.form.get('password')
        verify = request.form.get('verify')
        email = request.form.get('email')
        auth_cookie = request.form.get('auth_cookie')

        params = dict(username=username, password=password, verify=verify,
                      email=email, auth_cookie=auth_cookie, username_error='',
                      password_error='', verify_error='', email_error='',
                      user_unique_chk=True, have_error=False)

        check_user_info(params)

        if params['have_error']:
            # By using a dictionary, can now use the unpack operator and send
            # everything in the dictionary {self.render('signupapp.html, **params)}
            # versus the huge list of KVPs below.
            # Also - reset the passwords
            params['password'] = ''
            params['verify'] = ''

            return render_template('signup.html', **params)
        # Valid new account
        else:
            user = User(name=username, email=email, utype=USER_TYPE,
                        password_hash=User.hash_password(password))
            session.add(user)
            session.commit()

            # Add flashing...
            flash('User Created')

            # Send back a session cookie or cookie with a 30 day TTL
            # websession['username'] = user.serialize
            # Just store user ID versus serialized user object
            websession['user_id'] = user.uid
            websession['provider'] = 'Local'
            # Note - default lifetime is actually 31 days...
            websession.permanent = True if auth_cookie else False

        return redirect(url_for('signin'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Handle Google auth callback
    # If this request does not have `X-Requested-With` header, this could be a CSRF
    if not request.headers.get('X-Requested-With'):
        print('Debug/invalid header!')
        response = make_response(json.dumps('Invalid post header.'), 403)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Validate state token - does state query parameter match one stored in
    # session cookie?
    if request.args.get('state') != websession['state']:
        print('Debug/state check failed!')
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code - request.data is inbound data in a mimetype
    # flask doesn't understand delivered as a string
    auth_code = request.data
    try:
        # Exchange auth code for access token, refresh token, and ID token
        credentials = credentials_from_clientsecrets_and_code(CLIENT_SECRET_FILE,
                                        ['openid', 'profile', 'email'], auth_code)
        # Call Google API
        credentials.authorize(httplib2.Http())
    except FlowExchangeError:
        print('Debug/gconnect/obtain auth code failed!')
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except UnknownClientSecretsFlowError:
        print('Debug/gconnect/client secrets file describes unknown kind of flow!')
        response = make_response(json.dumps('Client Secrets file describes unknown kind of '
                                            'flow.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    except InvalidClientSecretsError:
        print('Debug/gconnect/client secrets file invalid!')
        response = make_response(json.dumps('Client Secrets file invalid.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Get profile info from ID token
    # Available fields or "claims":
    # - at_hash: Access Token hash, shouldn't need to use if using anticsrf state
    # - aud: Target audience for ID token, must match app's client ID!
    # - azp: Authorized presenter's client ID, not needed here
    # - email: User's email address; don't use as a primary key, use sub instead!
    # - email_verified: True if email was verified, otherwise false
    # - exp: ID token Expiration time (UNIX time in integer seconds)
    # - hd: User's hosted G Suite domain (Only if user belongs to a hosted domain)
    # - iat: ID token Issued at time (UNIX time in integer seconds)
    # - iss: Issuer Identifier, should be [https://]accounts.google.com
    # - name: User's full name (not guaranteed to be present)
    # - nonce: Returned if supplied before (to provide anti-replay functionality)
    # - picture: URL of user's profile picture (not guaranteed to be present)
    # - profile: URL of user's profile page (not guaranteed to be present)
    # - sub: Goolge unique user ID; reference user with this and not with email address!

    # Check that the access token is valid
    if not credentials.access_token:
        print('Debug/gconnect - empty access token!')
        response = make_response(json.dumps('Unknown error - missing access_toekn...'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if credentials.client_id != CLIENT_ID:
        print("Debug/gconnect/token Client ID doesn't match up with app's!")
        response = make_response(json.dumps("Token's Client ID doesn't match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Credentials object requires helper for (de-)serialization
    serialized_credentials = websession.get('credentials')
    stored_credentials = None
    if serialized_credentials:
        try:
            stored_credentials = OAuth2Credentials.from_json(serialized_credentials)
        except ValueError as e:
            pass
    print('stored_credentials:\n{}'.format(stored_credentials))

    # Verify that the access token is used for the intended user
    google_id = credentials.id_token['sub']
    if stored_credentials is not None and google_id != stored_credentials.id_token['sub']:
        print("Debug/gconnect/user ID doesn't match given user ID!")
        response = make_response(json.dumps("OAuth user ID doesn't match given user ID."), 401)
        response.header['Content-Type'] = 'application/json'
        return response

    if stored_credentials is not None and google_id == stored_credentials.id_token['sub']:
        print('Debug/gconnect/current user already connected!')
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Note - a Google ID Token must be validated unless retrieved directly from Google,
    # then can assume it's valid per Google docs

    # Debugging - check for refresh token
    # In the future could consider storing this to refresh access_tokens
    refresh_token = credentials.refresh_token
    if refresh_token:
        print('Received refresh token.')

    # Purge sensitive parts:
    credentials.refresh_token = None
    credentials.client_secret = None

    # Credentials object requires helper for (de-)serialization
    websession['credentials'] = credentials.to_json()

    # Get user info
    # This is sloppy - per Google, should retrieve discovery document from
    # https://accounts.google.com/.well-known/openid-configuration, look for key
    # "userinfo_endpoint" and then query that URL...
    # Also - should probably use a library for this and not do raw URL requests
    userinfo_endpoint = 'https://www.googleapis.com/oauth2/v3/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_endpoint, params=params)
    data = answer.json()

    username = data.get('given_name', '') + data.get('family_name', '')
    websession['provider'] = 'Google'
    websession['locale'] = data['locale']
    picture = data['picture']
    profile = data['profile']
    email = data['email']

    # Check if user in database and add if not
    # Per Google, email address can change and shouldn't be use to uniquely identify
    # user; instead use sub which is guaranteed to be unique
    try:
        user = session.query(User).filter_by(pid=google_id).one()
    except NoResultFound as e:
        user = None

    # Should also check to see if fields changed and then update...
    # Should also check for username conflict and create function that will mangle
    # username to make it unique
    if not user:
        user = User(name=username, email=email, utype=USER_TYPE, picture=picture,
                    profile=profile, pid=google_id)
        session.add(user)
        session.commit()

    websession['user_id'] = user.uid
    flash("You are now logged in as {}".format(username))

    response = make_response(json.dumps('Google login completed.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


# Disconnect - Revoke a current user's token and reset their websession
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    serialized_credentials = websession.get('credentials')
    credentials = None
    if serialized_credentials:
        try:
            credentials = OAuth2Credentials.from_json(serialized_credentials)
        except ValueError as e:
            pass

    if not credentials:
        print('Debug/gdisconnect - no credentials present, aborting...')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        credentials.revoke(httplib2.Http())
        print('User credentials successfully revoked')
    except TokenRevokeError as e:
        print('User credential revocation failed:  {}'.format(e))

        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    provider = websession.get('provider')
    if not provider:
        flash('You were not logged in.')
    elif provider == 'Google':
        gdisconnect()

        flash('You have been successfully logged out.  (Google)')
    elif provider == 'Local':
        flash('You have successfully been logged out.  (Compendium)')
    else:
        print('Error:  Provider "{}" not implemented'.format(provider))

    # Always purge fields in case there's left over junk in cookie:
    for field in ['credentials', 'locale', 'provider', 'state', 'user_id']:
        websession.pop(field, None)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

