from google.appengine.ext import db
import datetime
import hashlib
import hmac
import jinja2
import os
import webapp2

DATE_FMT = "%a %b %d, %Y at %H:%M:%S %z"
# Note:  This should be stored somewhere else and securely imported:
SECRET = 'topsecret!'

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

def hash_str(s):
    # Use HMAC instead - makes forging very difficult
    #return hashlib.md5(s).hexdigest()
    # Note - this default to using MD5 hash which is broken, for production
    #        use SHA2/256
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    #return "{},{}".format(s, hash_str(str(s)))
    # GAE treats "," specially within HTTP Cookies, use "|" instead
    return "{}|{}".format(s, hash_str(str(s)))

def check_secure_val(h):
    #val = h.split(',')[0]
    # GAE treats "," specially within HTTP Cookies, use "|" instead
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

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

class MainPage(Handler):
    def get(self):
        #self.render('hello.html')
        self.response.headers['Content-Type'] = 'text/plain'
        # Look for cookie with key of visits, if not there return 0:
        visits = 0
        visit_cookie_val = self.request.cookies.get('visits')
        if visit_cookie_val:
            cookie_val = check_secure_val(visit_cookie_val)
            if cookie_val:
                visits = int(cookie_val)
        visits += 1
        new_cookie_val = make_secure_val(str(visits))
        # Send updated cookie to client
        # Note - could use self.response.headers['Set-Cookie'] but this would overwrite
        # any existing value, we'd rather just add to the existing headers
        self.response.headers.add_header('Set-Cookie', 'visits={}'.format(new_cookie_val))
        if visits > 1000:
            self.write("You are the best ever!")
        else:
            self.write("You've been here {} times!".format(visits))

# Note - the URL path can be more than one level deep,
#        e.g., /hw2/rot13
app = webapp2.WSGIApplication([('/', MainPage),
                              ], debug=True)

