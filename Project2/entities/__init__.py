# GAE Datastore Entities (like Database record/row template)

####################################################################################################
# Entity Model
#===================================================================================================
# User 1-->M Blog(s)
# Blog 1-->M Comment(s)
####################################################################################################

# Dependencies:
from google.appengine.ext import db
import logging
import time
from utils import *

# Entity classes:
from User import User
from Blog import Blog
from Comment import Comment

