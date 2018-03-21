from google.appengine.ext import db
import datetime
import hashlib
import hmac
import jinja2
import logging
import os
import random
import re
import string
import time
import webapp2

# Constants
DATE_FMT = "%a %b %d, %Y at %H:%M:%S %z"
# Ideally would also include string.punctuation, but afraid some symbols may
# cause problems...
SALT_SET = string.letters + string.digits
#
# Note:  This should be stored somewhere else and securely imported:
#        Also, this should be a long random string with letters, numbers and symbols which
#        is machine generated and long - i.e., 50+ characters
SECRET = 'Inv@l1dS3cr3t:-('
#
VLD_USERNAME = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
VLD_PASSWORD = re.compile(r'^.{3,20}$')
# Instructor states that in his experience (as lead engineer at Reddit) this
# is good enough.  If the email isn't valid, the email program/tool will
# catch it.  Definitely some wisdom to his KISS thoughts.
VLD_EMAIL = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

def make_salt():
    return ''.join(random.choice(SALT_SET) for i in range(5))

# HASH(name + pw + salt),salt
def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    # Secure if SECRET secured
    h = hmac.new(SECRET, name+pw+salt, hashlib.sha256).hexdigest()
    # Not secure, is user figures out algorithm can easily replicate
    # h = hashlib.sha256(name + pw + salt).hexdigest()
    # <!> This is dangerous - revealing password parameter in plaintext, can't do in production!
    logging.debug('make_pw_hash - for name={}, pw={}, salt={}, created hash={}'.format(name, pw,
                  salt, h))
    return '%s|%s' % (h, salt)

def validate_pw(name, pw, h):
    _, _, salt = h.partition('|')
    chkh = make_pw_hash(name, pw, salt)
    logging.debug('validate_pw - for name={}, pw={}, hash={}, salt={}'.format(name, pw, h, salt))
    logging.debug('passed_hash = {}, calculated_hash = {}'.format(h, chkh))
    return chkh == h

def unique_username(username):
    q = db.Query(UserDB)
    # Are there entries in the DB?
    if q.get():
        # If I get a match, username already in DB
        # if db.GqlQuery('select * from UserDB where username = :1', username)
        # user_acct = db.GqlQuery('select * from UserDB where username = {}'.format(username)).get()
        user_acct = db.GqlQuery('select * from UserDB where username = :1', username).get()
        if user_acct:
            return False
    # Otherwise username is unique (empty DB, username not in DB)
    return True

def valid_username(username):
    return VLD_USERNAME.match(username)

def valid_password(password):
    return VLD_PASSWORD.match(password)

def valid_verify(password, verify):
    return password == verify

def valid_email(email):
    # Email optional - only validate if submitted
    if email is None or email == '':
        if email == '':
            logging.debug("no email address included ('')")
        elif email is None:
            logging.debug('no email address included (None)')
        # Should never get here
        else:
            assert True == False
        return True
    else:
        return VLD_EMAIL.match(email)

class UserDB(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    userid = db.IntegerProperty(required=True)
    # auto_now_add = Default to current date/time
    created = db.DateTimeProperty(auto_now_add=True)

# Shortcut so can just say self.write vs. self.response.out.write...
class Handler(webapp2.RequestHandler):
    def write(self, *arg, **kwarg):
        self.response.out.write(*arg, **kwarg)

    def render_str(self, template, **params):
        # Load template
        t = jinja_env.get_template(template)
        # Return rendered template
        return t.render(params)

    def render(self, template, **kwarg):
        self.write(self.render_str(template, **kwarg))

class SignupApp(Handler):
    def get(self):
        self.render('signupapp.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username=username, password=password, verify=verify, email=email,
                      username_error='', password_error='', verify_error='', email_error='')
        have_error = False

        if not valid_username(username):
            params['username_error'] = 'Invalid username - Must be from 3-20 characters' + \
                             ' consisting of a-z, A-Z, 0-9, _, -'
            have_error = True

        if not have_error and not unique_username(username):
            params['username_error'] = 'Username unavailable - already in use, please ' + \
                             'choose another username'
            have_error = True

        if not valid_password(password):
            params['password_error'] = 'Invalid password - Must be from 3-20 characters long'
            have_error = True

        if not valid_verify(password, verify):
            params['verify_error'] = "Passwords don't match"
            have_error = True

        if not valid_email(email):
            params['email_error'] = 'Invalid E-mail address - Must be name@domain.domain' + \
                          ' (e.g., george@yahoo.com)'
            have_error = True

        if have_error:
            # By using a dictionary, can now use the unpack operator and send
            # everything in the dictionary {self.render('signupapp.html, **params)}
            # versus the huge list of KVPs below.
            # Also - reset the passwords
            params['password'] = ''
            params['verify'] = ''
            self.render('signupapp.html', **params)
        # Valid new account
        else:
            # Create a secure hash of the password:
            password_hash = make_pw_hash(params['username'], params['password'])

            # Store account in database
            # See if there are entities in the DB
            q = db.Query(UserDB)
            if q.get():
                latest = db.GqlQuery('select * from UserDB order by created desc limit 1').get()
                # Set the next userid number to the latest + 1
                userid = latest.userid + 1
            # Otherwise, use the default userid number
            else:
                userid = 1001
            user_acct = UserDB(username=username, password=password_hash, email=email,
                               userid=userid)
            logging.debug('Signup/New Account - user_acct:  username = {}, '.format(username) + \
                          'password_hash = {}, email = {}, userid = {}'.format(password_hash,
                          email, userid))
            user_acct.put()
            #blogid = str(ent.key().id())

            # Create hash of userid for session cookie
            userid_hash = make_pw_hash(params['username'], str(userid))
            logging.debug('Signup/Userid_Hash - user_acct:  username = {}, userid = {},'.format(
                          username, userid) + ' userid_hash = {}'.format(userid_hash))

            # Create session cookie and send to client
            # Note - could use self.response.headers['Set-Cookie'] but this would overwrite
            # any existing value, we'd rather just add to the existing headers
            self.response.headers.add_header('Set-Cookie', 'userid={}|{}; Path=/'.format(userid,
                                             userid_hash))
            logging.debug('Signup/Set-Cookie - cookie-userid:  userid = {}, userid_hash = {}'.format(
                          userid, userid_hash))
            self.redirect('/creating')

class LogoutApp(Handler):
    def get(self):
        # Clear cookie
        self.response.headers.add_header('Set-Cookie', 'userid=; Path=/; expires=Thu, 01 Jan ' +
                                         '1970 00:00:00 GMT')
        logging.debug("Logout/Set-Cookie - delete cookie:  userid = ''; expires = Thu, 01 Jan " +
                      "1970 00:00:00 GMT")

        # Redirect to /signup
        self.redirect('/signup')

class LoginApp(Handler):
    def get(self):
        self.render('loginapp.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        params = dict(username=username, password=password, username_error='', password_error='',
                      auth_error='')
        have_error = False

        if not valid_username(username):
            params['username_error'] = 'Invalid username - Must be from 3-20 characters' + \
                             ' consisting of a-z, A-Z, 0-9, _, -'
            have_error = True

        if not valid_password(password):
            params['password_error'] = 'Invalid password - Must be from 3-20 characters long'
            have_error = True

        if have_error:
            params['password'] = ''
            self.render('loginapp.html', **params)
        # Acceptable credentials - check if valid
        else:
            # See if there are entities in the DB
            q = db.Query(UserDB)
            if q.get():
                user_acct = db.GqlQuery('select * from UserDB where username = :1', username).get()
            if user_acct:
                logging.debug('Submitted username ({}) found in datastore.'.format(
                              user_acct.username))
                # Now validate password
                if user_acct:
                    if validate_pw(username, password, user_acct.password):
                        logging.debug('Valid password entered for username ({}).'.format(
                                      user_acct.username))
                        # Create and send session cookie
                        # Create hash of userid for session cookie
                        userid_hash = make_pw_hash(params['username'], str(user_acct.userid))
                        logging.debug('Login/Userid_Hash - user_acct:  username = {}, '.format(
                                      username) + 'userid = {}, userid_hash = {}'.format(
                                      user_acct.userid, userid_hash))
    
                        # Create session cookie and send to client
                        self.response.headers.add_header('Set-Cookie', 'userid={}|{}; '.format(
                                                         user_acct.userid, userid_hash) + 'Path=/')
                        logging.debug('Signup/Set-Cookie - cookie-userid:  userid = {}, '.format(
                                      user_acct.userid) + 'userid_hash = {}'.format(userid_hash))
                        self.redirect('/welcome')
                    else:
                        logging.info('Invalid password entered for username ({}).'.format(
                                     user_acct.username))
            else:
                logging.info('Invalid username entered ({}) - not found in datastore.'.format(
                             username))
            # Invalid username and/or password
            params['password'] = ''
            params['auth_error'] = 'Invalid username and/or password'
            self.render('loginapp.html', **params)

class CreatingApp(Handler):
    def get(self):
        cookie = self.request.cookies.get('userid')
        if cookie:
            userid, _, _ = cookie.partition('|')
            logging.debug('Creating/Cookie - userid = {}'.format(userid))
            self.render('creating.html')
            while True:
                q = db.Query(UserDB)
                if q.get():
                    user_acct = db.GqlQuery('select * from UserDB where userid = :1', int(userid)).get()
                    if user_acct:
                        self.redirect('/welcome')
                        return
                logging.debug("Account hasn't been created yet - sleeping for 100ms...")
                time.sleep(0.100)
        else:
            self.redirect('/welcome')

class WelcomeApp(Handler):
    def get(self):
        cookie = self.request.cookies.get('userid')
        if cookie:
            userid, _, userid_hash = cookie.partition('|')
            logging.debug('Welcome/Cookie - userid = {}; userid_hash = {}'.format(userid,
                          userid_hash))

            # Lookup username by userid:
            q = db.Query(UserDB)
            if q.get():
                user_accts = db.GqlQuery('select * from UserDB order by created asc')
                for ua in user_accts:
                    logging.debug('Welcome/DB - ua:  ua.username = {}, '.format(ua.username) + \
                                  'ua.password_hash = {}, ua.email = {}, ua.userid = {},'.format(
                                  ua.password, ua.email, ua.userid) + ' ua.created = {}'.format(
                                  ua.created))
                user_acct = db.GqlQuery('select * from UserDB where userid = :1', int(userid)).get()
                logging.debug('Welcome/Query - username = {}, password_hash = {}, '.format(
                              user_acct.username, user_acct.password) + 'email = {}, '.format(
                              user_acct.email) + 'userid = {}, created = {}'.format(
                              user_acct.userid, user_acct.created))
                if user_acct:
                    username = user_acct.username
                    logging.debug('Welcome/Validate Cookie - checking...')
                    if userid_hash and validate_pw(username, userid, userid_hash):
                        self.render('welcome.html', username=username)
                        return
                    logging.debug('Welcome/Validate Cookie - failed')
        self.redirect('/signup')

class MainPage(Handler):
    def get(self):
        self.render('hello.html')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/creating', CreatingApp),
                               ('/login', LoginApp),
                               ('/logout', LogoutApp),
                               ('/signup', SignupApp),
                               ('/welcome', WelcomeApp)], debug=True)
