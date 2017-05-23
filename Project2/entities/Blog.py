from google.appengine.ext import db

# Blog Entity - for GAE Datastore
class Blog(db.Model):
    # Reference property to User (User 1-->M Blog(s))
    user = db.ReferenceProperty(User, collection_name='blogs')

    # General properties
    title = db.StringProperty(required=True)
    author = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    tags = db.StringProperty()
    # Note - limited to 1 MB
    picture = db.BlobProperty()
    likes = db.BlobProperty()
    dislikes = db.BlobProperty()
    # auto_now_add = Default to current date/time
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now_add=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

    @staticmethod
    def pkey(name='default'):
        return db.Key.from_path('Blogs', name)

