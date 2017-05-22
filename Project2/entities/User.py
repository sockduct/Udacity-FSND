from google.appengine.ext import db
import logging
from utils import *

# User Entity - for GAE Datastore
class User(db.Model):
    username = db.StringProperty(required=True)
    passwdhash = db.StringProperty(required=True)
    email = db.StringProperty()
    # auto_now_add = Default to current date/time
    created = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def pkey(group='default'):
        return db.Key.from_path('Users', group)

    # get_by_id is db.Model method
    @classmethod
    def by_id(cls, uid):
        user = cls.get_by_id(uid, parent=User.pkey())
        if user:
            logging.debug('Found user ({}) by uid={}.'.format(user.username, uid))
        else:
            logging.debug('No user found for uid={}.'.format(uid))
        return user

    # Get all User entities (DB objects) and retrieve one matching name
    @classmethod
    def by_username(cls, username):
        user = cls.all().filter('username =', username).get()
        #if user:
        #    logging.debug('Found user by username={}.'.format(username))
        #else:
        #    logging.debug('No user found for username={}.'.format(username))
        return user

    @classmethod
    def create(cls, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        passwdhash = make_passwdhash(username, password)
        email = kwargs.get('email')
        user = cls(parent=User.pkey(), username=username, passwdhash=passwdhash, email=email)
        user.put()
        #logging.debug('Creating account username={}, password_hash={}, email={}, entity_key={}, '
        #              'uid={}'.format(username, passwdhash, email, user.key(), user.key().id()))
        # Wait until user created in DB
        while True:
            if not cls.by_username(username):
                #logging.debug("Account hasn't been created yet - sleeping for 100ms...")
                time.sleep(0.100)
            else:
                break
        return user

    @classmethod
    def login(cls, username, password):
        user = cls.by_username(username)
        if user and validate_pw(username, password, user.passwdhash):
            return user

