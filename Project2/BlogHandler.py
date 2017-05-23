import datetime
from entities import User
import jinja2
import logging
from utils import *
import webapp2

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               extensions=['jinja2.ext.loopcontrols'], autoescape=True)

class BlogHandler(webapp2.RequestHandler):
    # Shortcut so can just say self.write vs. self.response.out.write:
    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render_str(self, template, **params):
        # Load template
        t = jinja_env.get_template(template)
        # Return rendered template
        return t.render(params)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

    def set_sec_cookie(self, ckey, cval, host, auth_cookie=None):
        sec_cval = make_sec_val(cval)
        # Production:
        # cookie = ('{}={}; Domain=accumulator-jrs.appspot.com; Path=/; '.format(ckey, sec_cval)
        #           'Secure; HttpOnly; SameSite=Strict')
        # Testing:
        # cookie = '{}={}; Path=/; '.format(ckey, sec_cval)
        # This is problematic as it doesn't escape special values:
        # self.response.headers.add_header('Set-Cookie', cookie)
        # webapp2 docs recommend using response.set_cookie method:
        # self.response.set_cookie(ckey, sec_cval, path='/', domain='accumulator-jrs.appspot.com',
        #                          secure=True, httponly=True, overwrite=True)
        logging.debug('set_sec_cookie/host={}'.format(host))
        if auth_cookie == 'remember':
            # Set persistent cookie to last for 30 days
            expiry = datetime.datetime.now() + datetime.timedelta(days=30)
        else:
            # Set session cookie
            expiry = None

        # Running on localhost for testing
        if str(host).startswith('localhost:'):
            self.response.set_cookie(ckey, sec_cval, path='/', expires=expiry)
        # Running on GCP
        else:
            self.response.set_cookie(ckey, sec_cval, path='/', domain='accumulator-jrs.appspot.com',
                                     secure=True, httponly=True, overwrite=True, expires=expiry)

        #logging.debug("Set_Sec_Cookie/Set-Cookie - create cookie:  {}={}; Path=/; ".format(ckey,
        #              sec_cval))

    def read_sec_cookie(self, ckey):
        cval = self.request.cookies.get(ckey)
        #logging.debug('Request to agent for cookie (key={}) yielded value={}'.format(
        #              ckey, cval))
        # Debugging code
        #if not cval:
        #    logging.debug("Agent doesn't have userid cookie")
        #elif chk_sec_val(cval):
        #    logging.debug('Successfully read and validated userid cookie')
        #else:
        #    logging.debug('Validation of userid cookie failed')
        #t1 = cval and chk_sec_val(cval)
        #t2 = chk_sec_val(cval)
        #logging.debug('{} and {} = {}'.format(cval, t2, t1))
        return cval and chk_sec_val(cval)

    def login(self, user, host, auth_cookie=None):
        self.set_sec_cookie('userid', str(user.key().id()), host, auth_cookie)

    def logout(self, host=None):
        # This is problematic as it doesn't escape special values:
        # self.response.headers.add_header('Set-Cookie', 'userid=; Path=/; expires=Thu, 01 Jan '
        #                                  '1970 00:00:00 GMT')
        # webapp2 docs recommend using response.delete_cookie method:
        if host:
            domain = str(host).split(':')[0]
        else:
            domain = None
        self.response.delete_cookie('userid', domain=domain)
        logging.debug('Logout/Delete_Cookie - userid')

    # Overriding webapp2.RequestHandler.initialize()
    def initialize(self, *args, **kwargs):
        webapp2.RequestHandler.initialize(self, *args, **kwargs)
        uid = self.read_sec_cookie('userid')
        # Debugging code
        #logging.debug('Read userid of {} from cookie'.format(uid))
        #if uid:
            #t1 = User.by_id(int(uid))
            #logging.debug('User.by_id({}) = {}'.format(uid, t1))
            #t2 = uid and t1
            #logging.debug('uid and User.by_id({}) = {}'.format(uid, t2))
        self.user = uid and User.by_id(int(uid))

