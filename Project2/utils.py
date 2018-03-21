import ConfigParser
# Belive fails because of circular dependency
# from entities import User, Blog, Comment
import entities
from google.appengine.ext import db
import hashlib
import hmac
import pickle
import string
import random
import re

####################################################################################################
# Constants
# Had too many problems with string.punctuation - creates corner cases
# Instead hand pick symbols which are OK
my_punctuation = '!#()*+,-.:;<>[]^_{}'
SALT_SET = string.letters + string.digits + my_punctuation
# Valid username and password formats
VLD_USERNAME = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
VLD_PASSWORD = re.compile(r'^.{10,40}$')
# Instructor states that in his experience (as lead engineer at Reddit) this
# is good enough.  If the email isn't valid, the email program/tool will
# catch it.  Definitely some wisdom to his KISS thoughts.
VLD_EMAIL = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

# Load HMAC Key - Note that GAE doesn't appear to allow reading from outside the app directory
config = ConfigParser.ConfigParser()
config.read('environment.cfg')
SECRET_KEY = config.get('seed', 'key')

def make_salt():
    return ''.join(random.choice(SALT_SET) for i in range(5))

# HASH(name + pw + salt),salt
def make_passwdhash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    # Don't need to use HMAC for password hash because shouldn't be accessible
    h = hashlib.sha256(name + pw + salt).hexdigest()
    # Don't reveal actual password
    #logging.debug('make_passwdhash - for name={}, pw={}, salt={}, created hash={}'.format(name, '*',
    #              salt, h))
    return '{}|{}'.format(h, salt)

def validate_pw(name, pw, h):
    _, _, salt = h.partition('|')
    chkh = make_passwdhash(name, pw, salt)
    # Don't reveal actual password
    #logging.debug('validate_pw - for name={}, pw={}, salt={}'.format(name, '*', salt))
    result = chkh == h
    #logging.debug('passed_hash = {}, calculated_hash = {}, match={}'.format(h, chkh, result))
    return result

# HASH(val + salt),salt
def make_sec_val(val, salt=None):
    if val:
        if not salt:
            salt = make_salt()
        # Use HMAC - Secure if SECRET_KEY secured
        h = hmac.new(SECRET_KEY, val+salt, hashlib.sha256).hexdigest()
        # Plain hash not secure, is user figures out algorithm can easily replicate
        # h = hashlib.sha256(val + salt).hexdigest()
        #logging.debug('Value passed:  value={}, Salt to use:  {}, Calculated HMAC:  {}'.format(val,
        #              salt, h))
        return '{}|{}|{}'.format(val, h, salt)

def chk_sec_val(secval):
    if secval:
        val, h, salt = secval.split('|')
        chkh = make_sec_val(val, salt)
        #logging.debug('Secure value passed:  value={}, HMAC={}, salt={}'.format(val, h, salt))
        result = chkh == secval
        #logging.debug('Calculated secure value:  {}, matches={}'.format(chkh, result))
        if result:
            return val

def valid_username(username):
    return VLD_USERNAME.match(username)

def valid_password(password):
    return VLD_PASSWORD.match(password)

def valid_verify(password, verify):
    return password == verify

def valid_email(email):
    # Email optional - only validate if submitted
    if email is None:
        logging.debug('no email address included (None)')
        return True
    elif email == '':
        logging.debug("no email address included ('')")
        return True
    else:
        return VLD_EMAIL.match(email)

def valid_post(post_id):
    key = db.Key.from_path('Blog', int(post_id), parent=entities.Blog.pkey())
    return db.get(key)

def valid_comment(post_id, comment_id):
    blog = valid_post(post_id)
    if blog:
        key = db.Key.from_path('Comment', int(comment_id), parent=blog.key())
        return db.get(key)

def check_user_info(params):
    if not valid_username(params['username']):
        params['username_error'] = ('Invalid username - Must be from 3-20 characters'
                                    ' consisting of a-z, A-Z, 0-9, _, -')
        params['have_error'] = True

    ### user = User.by_username(params['username'])

    # If this user already exists and there isn't another error
    if (params.get('user_unique_chk') and entities.User.by_username(params['username']) and not
            params['have_error']):
        params['username_error'] = ('Username unavailable - already in use, please '
                                    'choose another username')
        params['have_error'] = True

    if not valid_password(params['password']):
        params['password_error'] = 'Invalid password - Must be from 10-40 characters long'
        params['have_error'] = True

    if params.get('verify') and not valid_verify(params['password'], params['verify']):
        params['verify_error'] = "Passwords don't match"
        params['have_error'] = True

    if params.get('email') and not valid_email(params['email']):
        params['email_error'] = ('Invalid E-mail address - Must be name@domain.domain'
                                 ' (e.g., george@yahoo.com)')
        params['have_error'] = True

# Convert from stored pickled value to object
def get_stval(st_val):
    obj_val = pickle.loads(st_val)
    #logging.debug('get_stval - retrieved object {}'.format(obj_val))
    return obj_val

# Convert from object to pickled value (for storage)
def set_pval(obj_val):
    #logging.debug('set_pval - received object {}'.format(obj_val))
    st_val = pickle.dumps(obj_val)
    return st_val

def post_votes(blog):
    if blog.likes:
        likes = get_stval(blog.likes)
        #logging.debug('PostPage - likes for {}:  {}'.format(blog.title, likes))
    else:
        likes = set()
    if blog.dislikes:
        dislikes = get_stval(blog.dislikes)
        #logging.debug('PostPage - dislikes for {}:  {}'.format(blog.title, dislikes))
    else:
        dislikes = set()

    return likes, dislikes

