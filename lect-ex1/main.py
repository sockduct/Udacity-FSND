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

import cgi
import webapp2

#HTML_ESC = {'>': '&gt;', '<': '&lt;', '"': '&quot;', '&': '&amp;'}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
form='''
<form method="post">
    What is your birthday?
    <br>
    <label>Month <input type="text" name="month" value="{month}"></label>
    <label>Day <input type="text" name="day" value="{day}"></label>
    <label>Year <input type="text" name="year" value="{year}"></label>
    <div style="color: red">{error}</div>
    <br>
    <br>
    <input type="submit">
</form>
'''
# <div style="color: red">%(error)s</div>
# <div style="color: red">{error}</div>

# Use cgi module instead:
#def escape_html(s):
#    temp_s = []
#    for c in s:
#        if c in HTML_ESC:
#            c = HTML_ESC[c]
#        temp_s.append(c)
#    return ''.join(temp_s)
#
def escape_html(s):
    return cgi.escape(s, quote=True)

def valid_month(month):
    brd_months = dict((m[0:3].lower(), m) for m in MONTHS)
    if month and len(month) >= 3:
        if month[0:3].lower() in brd_months:
            return brd_months[month[0:3].lower()]

def valid_day(day):
    if day and day.isdigit():
        num_day = int(day)
        if num_day >= 1 and num_day <= 31:
            return num_day

def valid_year(year):
    if year and year.isdigit():
        num_year = int(year)
        if num_year >= 1900 and num_year <= 2017:
            return num_year

class MainPage(webapp2.RequestHandler):
    def write_form(self, error='', month='', day='', year=''):
        # self.response.out.write(form % {'error': error})
        # If retain original user input without sanitizing:
        # self.response.out.write(form.format(error=error,
        #                                    month=escape_html(month),
        #                                    day=escape_html(day),
        #                                    year=escape_html(year)))
        self.response.out.write(form.format(error=error, month=month,
                                            day=day, year=year))

    def get(self):
        # Default Content-Type is 'text/html' - change to that or comment
        # out to send HTML
        # response is what goes out (e.g., to browser)
        # self.response.headers['Content-Type'] = 'text/plain'
        self.response.headers['Content-Type'] = 'text/html'
        # self.response.write('Hello, WebApp World!')
        # self.response.out.write(form)
        self.write_form()

    def post(self):
        # Get input
        user_month = self.request.get('month')
        user_day = self.request.get('day')
        user_year = self.request.get('year')

        # Validate input
        month = valid_month(user_month)
        day = valid_day(user_day)
        year = valid_year(user_year)
        if not(month and day and year):
            # self.response.out.write(form)
            # If variable is None, replace with ''
            month = '' if not month else month
            day = '' if not day else day
            year = '' if not year else year
            self.write_form("That doesn't look valid to me, friend.",
                           month, day, year)
            # If want to display original user input
            # self.write_form("That doesn't look valid to me, friend.",
            #                user_month, user_day, user_year)
        else:
            self.redirect('/thanks')

class ThanksHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Thanks! That's a totally valid day!")

#class TestHandler(webapp2.RequestHandler):
    # Use "get" for GET method and "post" for POST method
#    def post(self):
        # request is what comes in (e.g., from browser)
#        q = self.request.get('q')
        # Show received information
#        self.response.out.write(q)
        # Show what actual raw request looks like:
        # self.response.headers['Content-Type'] = 'text/plain'
        # self.response.out.write(self.request)

# app = webapp2.WSGIApplication([('/', MainPage), ('/testform', TestHandler)],
app = webapp2.WSGIApplication([('/', MainPage), ('/thanks', ThanksHandler)],
                              debug=True)

