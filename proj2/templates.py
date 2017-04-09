# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import jinja2
import os
import webapp2

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

form_html = '''
<form>
    <h2>Add a Food</h2>
    <input type='text' name='food'>
    %s
    <button>Add</button>
</form>
'''
# <input...\n%s\n<button...

hidden_html = '''
<input type='hidden' name='food' value='%s'>
'''
# <input type='hidden' name='food' value='{}'>

# item_html = '<li>{}</li>'
item_html = '<li>%s</li>'

shopping_list_html = '''
<br>
<br>
<h2>Shopping List</h2>
<ul>
%s
</ul>
'''
# <ul>\n{}\n</ul>

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
        # self.write('Hello, Project 2!')
        # self.write(form_html)
        output = form_html
        output_hidden = ''
        # items will be a list of all the food parameters in the URL
        items = self.request.get_all('food')
        if items:
            output_items = ''
            for item in items:
                output_hidden += hidden_html % item
                output_items += item_html % item
            output_shopping = shopping_list_html % output_items
            output += output_shopping
        output = output % output_hidden

        #if items:
        #    output_items = ''
        #    for item in items:
        #        output_hidden += hidden_html.format(item)
        #        output_items += item_html.format(item)
        #    output_shopping = shopping_list_html.format(output_items)
        #    output += output_shopping
        #output = output.format(output_hidden)

        self.write(output)

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)

