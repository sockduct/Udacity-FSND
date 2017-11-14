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
# * TBD...
#
'''SQLAlchemy representation of database models for web application.'''

###################################################################################################
#
# Using the SQLAlchemy ORM, we define classes which map to database tables
# To create table entries:
#       <entry> = <Class>(<column1>=<value>, <column2>=<value>[, ...])
#
###################################################################################################

# Imports
from itsdangerous import (TimedJSONWebSignatureSerializer as TJWS_Serializer, BadSignature,
                          SignatureExpired)
import os
# Password/hash management
from passlib.context import CryptContext
# SQLAlchemy extension to map classes to database tables
from sqlalchemy.ext.declarative import declarative_base
# SQLAlchemy database table column type and related column data types
from sqlalchemy import (Column, Enum, ForeignKey, Integer, String, Text)
# For foreign key relationships and mapper
from sqlalchemy.orm import relationship
# SQLAlchemy module to connect to underlying database
from sqlalchemy import create_engine

# Globals
# Hashing
PasswordContext = CryptContext(schemes=['bcrypt'], deprecated='auto')
# Random Secret Key
# Note - drawback of this approach is everything based on it becomes invalid upon
# system restart
# Choose 32 as using SHA256 so want 256 bits of entropy (32 * 8)
SecretKey = os.urandom(32)
# SQLAlchemy setup - this is the base class that our model classes will be
# derived from
Base = declarative_base()


# To do - Ideally create another class to represent providers (Google, Facebook,
# Microsoft, ...); a user can then optionally be linked to one or more providers
class User(Base):
    # DB table name
    __tablename__ = 'user'

    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(250), nullable=False)
    utype = Column(Enum('user', 'admin', name='user_types'), nullable=False)
    # Picture is a URL given by the provider (Google)
    picture = Column(String(250))
    # Profile is a URL given by the provider (Google)
    profile = Column(String(250))
    # Pid is a unique user ID from the provider (Google, pid=sub)
    pid = Column(Integer, unique=True)
    password_hash = Column(String(100))
    uid = Column(Integer, primary_key=True)

    def __repr__(self):
        if self.picture:
            if len(self.picture) > 33:
                repr_picture = self.picture[:33] + '...'
            else:
                repr_picture = self.picture
        else:
            repr_picture = None

        if self.profile:
            if len(self.profile) > 33:
                repr_profile = self.profile[:33] + '...'
            else:
                repr_profile = self.profile
        else:
            repr_profile = None

        return ('<User(name={}, email={}, utype={}, uid={}, password_hash=*, picture={}, '
                'profile={}, pid={})>'.format(self.name, self.email, self.utype, self.uid,
                                              repr_picture, repr_profile, self.pid))

    def gen_auth_token(self):
        # Default expiration is one hour - can pass in parameter to change if desired
        s = TJWS_Serializer(SecretKey)

        return s.dumps(self.serialize)

    # Future improvement could be to override __init__ or make alternate "constructor"
    # with @classmethod which accepts a password and stores a hash in the instance
    @staticmethod
    def hash_password(password):
        # This might make sense if class had an __init__ method:
        # self.password_hash = PasswordContext.hash(password)
        # If change to above, need to get rid of staticmethod decorator and add
        # self as parameter
        return PasswordContext.hash(password)

    @staticmethod
    def verify_auth_token(token):
        s = TJWS_Serializer(SecretKey)
        try:
            user = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token

        # Same format as if calling self.serialize
        return user

    def verify_password(self, password):
        return PasswordContext.verify(password, self.password_hash)

    # Serialize function to support JSON
    @property
    def serialize(self):
        '''Return object data in easily serializable format'''
        return {
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
            'uid': self.uid
        }


# Parent class for 1:Many
class Category(Base):
    __tablename__ = 'category'

    name = Column(String(50), nullable=False, unique=True)
    cid = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.uid'))
    user = relationship(User)
    # Doesn't work without quotes around Item - get syntax error
    items = relationship('Item', order_by='Item.name', back_populates='category')

    def __repr__(self):
        repr_items = ''
        if self.items:
            for i in self.items:
                repr_items += '\t{}\n'.format(i)

            return '<Category(name={}, cid={}, user_id={}, items:\n{})>'.format(self.name,
                    self.cid, self.user_id, repr_items)
        else:
            repr_items = None

            return '<Category(name={}, cid={}, user_id={}, items={})>'.format(self.name,
                    self.cid, self.user_id, repr_items)

    @property
    def serialize(self):
        '''Return object data in easily serializable format'''

        return {
            'name': self.name,
            'cid': self.cid,
            'user_id': self.user_id
        }


# Child class for 1:Many
class Item(Base):
    __tablename__ = 'item'

    name = Column(String(50), nullable=False, unique=True)
    # This picture is an uploaded image file
    picture = Column(String(300))
    description = Column(Text)
    iid = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('category.cid'))
    category = relationship('Category', back_populates='items')
    user_id = Column(Integer, ForeignKey('user.uid'))
    user = relationship(User)

    def __repr__(self):
        if self.picture:
            repr_picture = '<image_binary>'
        else:
            repr_picture = None
        if self.description:
            if len(self.description) > 33:
                repr_description = self.description[:33] + '...'
            else:
                repr_description = self.description
        else:
            repr_description = None

        return ('<Item(name={}, picture={}, iid={}, category_id={}, category_name={}, '
                'user_id={}, description={}>'.format(self.name, repr_picture, self.iid,
                self.category_id, self.category.name, self.user_id, repr_description))

    @property
    def serialize(self):
        '''Return object data in easily serializable format'''

        return {
            'name': self.name,
            'picture': self.picture,
            'description': self.description,
            'iid': self.iid,
            'category_id': self.category_id,
            'category_name': self.category.name,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)

