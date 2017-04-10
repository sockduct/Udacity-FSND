import jinja2
import os
import re
import webapp2

ANLOWER = 'abcdefghijklmnopqrstuvwxyz'
ANUPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
VLD_USERNAME = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
VLD_PASSWORD = re.compiel(r'^.{3,20}$')
VLD_EMAIL = re.compile(r'^[\S]+@[\S]+.[\S]+$')

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

def valid_user(username):
    return VLD_USERNAME.match(username)

def valid_password(password):
    return VLD_PASSWORD.match(password)

def valid_verify(password, verify):
    return password == verify

def valid_email(email):
    # Email optional - only validate if submitted
    if email is None or email == '':
        return True
    else:
        return VLD_EMAIL.match(email)

def rot13(text):
    rot13_text = []
    #for line in text:
    #    print('Processing line {}'.format(line))
    for char in text:
        #print('Processing char {}'.format(char))
        if char.islower():
            number = (ANLOWER.index(char) + 13) % 26
            char = ANLOWER[number]
        elif char.isupper():
            number = (ANUPPER.index(char) + 13) % 26
            char = ANUPPER[number]
        rot13_text.append(char)
    return ''.join(rot13_text)

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

class SignupApp(Handler):
    def get(self):
        self.render('signupapp.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        if not valid_username(username):
            username_error = 'Invalid username - Must be from 3-20 characters consisting of a-a, A-Z, 0-9, _, -'
        else:
            username_error = None
        if not valid_password(password):
            password_error = 'Invalid password - Must be from 3-20 characters long'
        else:
            password_error = None
        if not valid_verify(password, verify):
            verify_error = "Passwords don't match"
        else:
            verify_error = None
        if not valid_email(email):
            email_error = 'Invalid E-mail address - Must be name@domain.domain (e.g., george@yahoo.com)'
        else:
            email_error = None

        if not username_error and not password_error and not verify_error and not
                email_error:
            x
        else:
            y

        self.render('signupapp.html', text=text)

class Rot13App(Handler):
    def get(self):
        self.render('rot13app.html')

    def post(self):
        text = self.request.get('text')
        text = rot13(text)
        self.render('rot13app.html', text=text)

class MainPage(Handler):
    def get(self):
        self.render('hello.html')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/rot13', Rot13App),
                               ('/signup', SignupApp)], debug=True)

