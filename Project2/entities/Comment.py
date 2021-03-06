from google.appengine.ext import db
# Causes circular dependency:
# from Blog import Blog
import Blog

# Note - Comments should be linked to their respective Blog post using its key as their parent
# Comment Entity - for GAE Datastore
class Comment(db.Model):
    # Reference property to Blog (Blog 1-->M Comment(s))
    blog = db.ReferenceProperty(Blog.Blog, collection_name='comments')

    # General properties
    author = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    # auto_now_add = Default to current date/time
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now_add=True)

