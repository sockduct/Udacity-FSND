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

class MainPage(Handler):
    def get(self):
        items = self.request.get_all('food')
        self.render('shopping_list.html', items=items)

class FizzBuzzHandler(Handler):
    def get(self):
        # 0 below is default value
        n = self.request.get('n', 0)
        n = n and int(n)
        self.render('fizzbuzz.html', n=n)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/fizzbuzz', FizzBuzzHandler)], debug=True)

