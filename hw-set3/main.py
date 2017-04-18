from google.appengine.ext import db
import datetime
import jinja2
import os
import webapp2

DATE_FMT = "%a %b %d, %Y at %H:%M:%S %z"

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

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

# Create Google App Engine Datastore Entity
class BlogDB(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    # auto_now_add = Default to current date/time
    created = db.DateTimeProperty(auto_now_add=True)
    entry = db.IntegerProperty(required=True)

class BlogApp(Handler):
    def get(self):
        blogs = db.GqlQuery('select * from BlogDB order by created desc limit 10')
        jinja_env.globals['now'] = datetime.datetime.now().strftime(DATE_FMT)
        self.render('main_blog.html', blogs=blogs)

class NewBlogApp(Handler):
    def render_blog(self, subject='', content='', error='', blogid=''):
        self.render('new_blog.html', subject=subject, content=content, error=error, blogid=blogid)

    def get(self):
        blogid = self.request.get('blogid')
        self.render_blog(blogid=blogid)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            # See if there are entities in the DB
            q = db.Query(BlogDB)
            if q.get():
                latest = db.GqlQuery('select * from BlogDB order by created desc limit 1')
                # Set the next entry number to the latest + 1
                entry = latest[0].entry + 1
            # Otherwise, use the default entry number
            else:
                entry = 1001
            ent = BlogDB(subject=subject, content=content, entry=entry)
            ent.put()
            #blogid = str(ent.key().id())
            # Need to redir to permalink, e.g., /blog/1001
            self.redirect('/blog/' + str(entry))
        else:
            error = 'We need both a title and an entry!'
            self.render_blog(subject, content, error)

class ViewBlogApp(Handler):
    def get(self, entry):
        blogs = db.GqlQuery('select * from BlogDB where entry={}'.format(entry))
        jinja_env.globals['now'] = datetime.datetime.now().strftime(DATE_FMT)
        self.render('main_blog.html', blogs=blogs)

class MainPage(Handler):
    def get(self):
        self.render('hello.html')

# Note - the URL path can be more than one level deep,
#        e.g., /hw2/rot13
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog', BlogApp),
                               ('/blog/newpost', NewBlogApp),
                               (r'/blog/(\d+)', ViewBlogApp),
                              ], debug=True)

