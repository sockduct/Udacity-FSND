#!/usr/bin/env python
# -*- coding: ascii -*-
###################################################################################################
'''Test views.py functionality'''

# Future Imports - Must be first, provides Python 2/3 interoperability
from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
from __future__ import division             # 3/2 == 1.5, 3//2 == 1
from __future__ import absolute_import      # prevent implicit relative imports in v2.x
from __future__ import unicode_literals     # all string literals treated as unicode strings

# Imports
import requests
import sys

# Globals
TIMEOUT = 2
site = 'http://localhost:5000'
routes = {'/': {'methods': ['GET']},
          '/catalog': {'methods': ['GET']},
          '/api/v0/catalog': {'methods': ['GET']},
          '/catalog/add': {'methods': ['GET', 'POST']},
          '/api/v0/catalog/create': {'methods': ['POST']},
          '/catalog/edit/{}': {'methods': ['GET', 'POST'], 'params': [0]},
          '/api/v0/catalog/read/{}': {'methods': ['GET'], 'params': [0]},
          '/api/v0/catalog/update/{}': {'methods': ['POST'], 'params': [0]},
          '/catalog/delete/{}': {'methods': ['GET', 'POST'], 'params': [0]},
          '/api/v0/catalog/delete/{}': {'methods': ['POST'], 'params': [0]},
          '/catalog/category/{}': {'methods': ['GET'], 'params': [0]},
          '/api/v0/catalog/category/{}': {'methods': ['GET'], 'params': [0]},
          '/clientOAuth': {'methods': ['GET']},
          '/oauth/{}': {'methods': ['POST'], 'params': ['google']},
          '/token': {'methods': ['GET']},
          '/signin': {'methods': ['GET', 'POST']},
          '/signout': {'methods': ['GET']},
          '/signup': {'methods': ['GET', 'POST']}}

for route in routes:
    for method in routes[route]['methods']:
        if method == 'GET' or method == 'POST':
            if routes[route].get('params'):
                ### For now assuming only one parameter!
                ### print('Found param of {}...'.format(routes[route]['params'][0]))
                target = site + route.format(routes[route]['params'][0])
            else:
                target = site + route
            print('Sending {} request to {}, received:'.format(method, target))
            response = getattr(requests, method.lower())(target, timeout=TIMEOUT)
            if response.status_code == 500:
                sys.exit('Unhandled exception by site {}...'.format(site))
            print('Status Code:  {}'.format(response.status_code))
            print('Content Type:  {}'.format(response.headers['content-type']))
            print('First Line of Content:  {!r}'.format(response.text[:80]))
            print('-=-' * 25)
        else:
            sys.exit('Method {} not implemented.'.format(method))

