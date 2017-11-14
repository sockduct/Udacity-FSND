###################################################################################################
#
# Using the SQLAlchemy ORM, we define classes which map to database tables
# To create table entries:
#       <entry> = <Class>(<column1>=<value>, <column2>=<value>[, ...])
#
###################################################################################################

# Imports
# SQLAlchemy extension to map classes to database tables
from sqlalchemy.ext.declarative import declarative_base
# SQLAlchemy database table column type and related column data types
from sqlalchemy import Column, Integer, String

###################################################################################################
# Don't believe these are needed in models - just in views
# SQLAlchemy database handle to interact with underlying database
# from sqlalchemy.orm import sessionmaker
# x
# from sqlalchemy.orm import relationship
###################################################################################################

# SQLAlchemy module to connect to underlying database
from sqlalchemy import create_engine
# x
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature,
                         SignatureExpired)
# Secure password hash library
from passlib.apps import custom_app_context as pwd_context
import random
import string

# SQLAlchemy setup - this is the base class that our model classes will be
# derived from
Base = declarative_base()

# x
secret_key = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase +
                     string.digits) for x in xrange(32))

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    # In SQLite and PostgreSQL you can get away without specifying a length,
    # but in other databases you can't!
    username = Column(String, index=True)
    fullname = Column(String)
    password_hash = Column(String)

    def __repr__(self):
        return "<User(username='{}', fullname='{}', password_hash='{}')>".format(self.username,
                    self.fullname, self.password_hash)

    @property
    def serialize(self):
        '''Return object data in easily serializable format'''
        return {
            'username': self.username,
        }

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    # Expiration is 600 seconds or 10 minutes
    def generate_auth_token(self, expiration=600):
        # Timed JSON Web Signature Serializer - tjwss
    	tjwss = Serializer(secret_key, expires_in = expiration)
    	return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        # Timed JSON Web Signature Serializer - tjwss
    	tjwss = Serializer(secret_key)
    	try:
    		data = tjwss.loads(token)
    	except SignatureExpired:
    		#Valid Token, but expired
    		return None
    	except BadSignature:
    		#Invalid Token
    		return None
    	user_id = data['id']
    	return user_id


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    picture = Column(String)
    description = Column(String)
    price = Column(String)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'category': self.category,
            'picture': self.picture,
            'price': self.price,
            'description': self.description
        }


# SQLAlchemy setup - create an instance of a connection to the underlying
# database
engine = create_engine('sqlite:///catalog.db')
# Check for existence of user defined classes/tables, if not present then create
# them
Base.metadata.create_all(engine)

