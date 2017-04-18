from google.appengine.ext import db
import jinja2
import os
import webapp2

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
class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    # auto_now_add = Default to current date/time
    created = db.DateTimeProperty(auto_now_add=True)

class ASCIIApp(Handler):
    def render_ascii(self, title='', art='', error=''):
        arts = db.GqlQuery('select * from Art order by created desc')
        self.render('asciiapp.html', title=title, art=art, error=error, arts=arts)

    def get(self):
        self.render_ascii()

    def post(self):
        title = self.request.get('title')
        art = self.request.get('art')

        if title and art:
            a = Art(title=title, art=art)
            a.put()
            # self.redirect('/thanks')
            self.redirect('/ascii')
        else:
            error = 'We need both a title and ASCII artwork!'
            self.render_ascii(title, art, error)

class ThanksApp(Handler):
    def get(self):
        self.render('thanks.html')

class MainPage(Handler):
    def get(self):
        self.render('hello.html')

# Note - the URL path can be more than one level deep,
#        e.g., /hw2/rot13
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/ascii', ASCIIApp),
                               ('/thanks', ThanksApp)], debug=True)

