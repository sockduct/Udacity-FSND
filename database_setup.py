#!/usr/bin/env python
# -*- coding: ascii -*-
###################################################################################################
#
# Python version(s) used/tested:
# * Python 2.7.12-32 on Ubuntu 16.04.2 LTS
# * Python 2.7.13-32 on Windows 7
#
'''Script to populate database.'''

# Imports
# My database table classes
from models import Category, Item, User
# SQLAlchemy extension to map classes to database tables
## from sqlalchemy.ext.declarative import declarative_base
# SQLAlchemy database handle to interact with underlying database
from sqlalchemy.orm import sessionmaker
# For foreign key relationships and mapper
## from sqlalchemy.orm import relationship
# SQLAlchemy module to connect to underlying database
from sqlalchemy import create_engine


# Globals
# SQLAlchemy setup - create an instance of a connection to the underlying database
engine = create_engine('sqlite:///catalog.db')
# Create ORM handle to underlying database
DBSession = sessionmaker(bind=engine)
# Used to interact with underlying database
session = DBSession()

# Database data
user_data = {'admin': {'email': 'admin@localhost', 'utype': 'admin'},
             'user': {'email': 'user@localhost', 'utype': 'user'}}
category_data = ['Soccer', 'Basketball', 'Baseball', 'Frisbee', 'Snowboarding', 'Rock Climbing',
                 'Foosball', 'Skating', 'Hockey', 'Dancing']
item_data = {'Stick': dict(picture='/static/uploads/hockey_stick.jpg', category='Hockey',
                           description='Phenomenal curve!'),
             'Goggles': dict(category='Snowboarding', description=('Latest UV protection '
                                                                   'built-in.')),
             'Snowboard': dict(category='Snowboarding', description=('Best for any terrain and '
                               'conditions.  All-mountain snowboards perform anywhere on a '
                               'mountain - groomed runs, backcountry, even park and pipe.  '
                               'They may be directional (meaning downhill only) or twin-tip '
                               '(for riding switch, meaning either direction).  Most boarders '
                               'ride all-mountain boards.  Because of their versatility, '
                               'all-mountain boards are good for beginners who are still '
                               'learning what terrain they like.')),
             'Shinguards': dict(category='Soccer', description='Durable plastic compound.'),
             'Frisbee': dict(category='Frisbee', description='Designed for maximum distance.'),
             'Bat': dict(category='Baseball', description='Genuine leather construction.'),
             'Jersey': dict(category='Soccer', description='Includes numbers.'),
             'Cleats': dict(category='Soccer', description='All-season.'),
             'Shoes': dict(category='Dancing', description=('Made of high quality supple '
                                                            'leather.'))}
default_photo = '/static/img/items-generic.jpg'


#Populate an empty database
users = session.query(User).all()
categories = session.query(Category).all()
items = session.query(Item).all()

if users == []:
    for user in user_data:
        db_user = User(name=user, email=user_data[user]['email'],
                       utype=user_data[user]['utype'])
        session.add(db_user)
    session.commit()

# Get admin user ID
user = session.query(User).filter_by(name='admin').one()

if categories == []:
    for category in category_data:
        db_category = Category(name=category, user_id=user.uid)
        session.add(db_category)
    session.commit()

if items == []:
    for item in item_data:
        category = session.query(Category).filter_by(name=item_data[item]['category']).one()
        if item_data[item].get('picture'):
            picture = item_data[item]['picture']
        else:
            picture = default_photo
        db_item = Item(name=item, picture=picture, user_id=user.uid,
                       category_id=category.cid, description=item_data[item]['description'])
        session.add(db_item)
    session.commit()

