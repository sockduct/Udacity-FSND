Google App Engine w/ Python App

Description:
App to accept blogs and save into GAE database.  Blogs then displayed on main page.  Uses Jinja2 templates to render HTML pages.

Methods:
* / - Main Page, Hello Greeting
* /blog - Blog app/page, displays 10 most recent blog entries
* /blog/newpost - Allow submission of new blog entry, stored in GAE database.  Upon successful entry, send to /blog/id# ([0-9]+)
* /blog/[0-9]+ - Blog entry permalink, displayed upon successful blog submission.  Can also go here directly to view a specific blog.

