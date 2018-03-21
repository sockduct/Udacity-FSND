#!/usr/bin/env python
# -*- coding: ascii -*-
###################################################################################################

'''Script to facilitate interactive database querying use SQLAlchemy.  Invoke
   using python -i <script.py>.'''

# Future Imports - Must be first, provides Python 2/3 interoperability
from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
from __future__ import division             # 3/2 == 1.5, 3//2 == 1
from __future__ import absolute_import      # prevent implicit relative imports in v2.x
from __future__ import unicode_literals     # all string literals treated as unicode strings

# Imports
import os
# My database table classes
from models import Base, Category, Item, User
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
# Use SQLite:
# DB_PATH = os.path.join(os.path.dirname(__file__), 'catalog.db')
# engine = create_engine('sqlite:///' + DB_PATH)
# Use PostgreSQL, with user catalog:
engine = create_engine('postgresql+psycopg2://catalog:NEKpPllvkcVEP4W9QzyIgDbKH15NM1I96BclRWG5@/catalog')
# Create ORM handle to underlying database
DBSession = sessionmaker(bind=engine)
# Used to interact with underlying database
session = DBSession()

print('\n' + '-=-' * 25)
print('SQLAlchemy database session object created as "session" connected to "catalog.db"')
print('ORM classes for database tables:  User, Category, Item')
print('\nExample query:  session.query(Category).order_by(Category.name).all()\n')

