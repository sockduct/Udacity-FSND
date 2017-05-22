import datetime
from entities import User, Blog, Comment
from google.appengine.ext import db
import jinja2
import logging
import os
import pickle
import time
from utils import *
import webapp2

####################################################################################################
# To Do
#===================================================================================================
# * Add delay after deleting post (maybe after deleting comment too) so it doesn't temporarily show
#   up when user is directed back to landing page
#
####################################################################################################
# Constants
DATE_FMT = "%a %b %d, %Y at %H:%M:%S %z"

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
        t1 = cval and chk_sec_val(cval)
        t2 = chk_sec_val(cval)
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
        if uid:
            t1 = User.by_id(int(uid))
            #logging.debug('User.by_id({}) = {}'.format(uid, t1))
            t2 = uid and t1
            #logging.debug('uid and User.by_id({}) = {}'.format(uid, t2))
        self.user = uid and User.by_id(int(uid))

class SignupPage(BlogHandler):
    def get(self):
        self.render('signup.html')

    def post(self):
        host = self.request.host
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        auth_cookie = self.request.get('auth_cookie')

        params = dict(host=host, username=username, password=password, verify=verify, email=email,
                      auth_cookie=auth_cookie, username_error='', password_error='',
                      verify_error='', email_error='', user_unique_chk=True, have_error=False)

        check_user_info(params)

        if params['have_error']:
            # By using a dictionary, can now use the unpack operator and send
            # everything in the dictionary {self.render('signupapp.html, **params)}
            # versus the huge list of KVPs below.
            # Also - reset the passwords
            params['password'] = ''
            params['verify'] = ''
            self.render('signup.html', **params)
        # Valid new account
        else:
            self.register(**params)

    def register(self, **params):
        user = User.create(**params)
        self.login(user, params['host'], params['auth_cookie'])
        self.redirect('/welcome')

class SignoutPage(BlogHandler):
    def get(self):
        # From initialize(), if I have a valid user:
        if self.user:
            username = self.user.username
            host = self.request.host
            self.logout(host)
            self.render('goodbye.html', username=username)
        # Redirect to Home/Landing Page
        else:
            self.redirect('/')

class SigninPage(BlogHandler):
    def get(self):
        redirect = self.request.get('redirect')
        if redirect:
            jinja_env.globals['redirect'] = '/' + redirect
        self.render('signin.html')

    def post(self):
        host = self.request.host
        username = self.request.get('username')
        password = self.request.get('password')
        auth_cookie = self.request.get('auth_cookie')

        params = dict(username=username, password=password, auth_cookie=auth_cookie,
                      username_error='', password_error='', auth_error='', have_error=False)

        check_user_info(params)

        if params['have_error']:
            logging.debug('SigninPage - authentication error')
            params['password'] = ''
            self.render('signin.html', **params)
        # Acceptable credentials - check if valid
        else:
            logging.debug('SigninPage - attempting login...')
            user = User.login(username, password)
            if user:
                self.login(user, host, auth_cookie)
                self.render('welcome.html', username=username)
            else:
                # Invalid username and/or password
                params['password'] = ''
                params['auth_error'] = 'Invalid username and/or password'
                self.render('signin.html', **params)

class WelcomePage(BlogHandler):
    def get(self):
        # From initialize(), if I have a valid user:
        if self.user:
            self.render('welcome.html', username=self.user.username)
        else:
            self.redirect('/signin')

class MainPage(BlogHandler):
    def get(self):
        # Limit to 9 or 10 and have previous/next buttons?
        blogs = Blog.all().order('-created')
        jinja_env.globals['now'] = datetime.datetime.now().strftime(DATE_FMT)
        jinja_env.globals['bcount'] = blogs.count()
        if self.user:
            jinja_env.globals['userauth'] = True
            jinja_env.globals['user'] = self.user.username
        else:
            jinja_env.globals['userauth'] = False
        self.render('landing.html', blogs=blogs)

# Create or Update Post
class CUPostPage(BlogHandler):
    def get(self):
        logging.debug('CUPostPage/get/entered...')
        if self.user:
            post_id = self.request.get('post_id')
            entry = self.request.get('entry')
            comment_id = self.request.get('comment_id')
            jinja_env.globals['user'] = self.user.username

            if entry == 'comment':
                iscomment = True
            else:
                iscomment = False

            # Sanity checks:
            if post_id:
                # Look up post_id:
                blog = valid_post(post_id)
                if not blog:
                    self.error(404)
                    return
            else:
                blog = None
            ### valid_comment might need some work on parent path...
            if comment_id:
                # Look up comment_id:
                comment = valid_comment(post_id, comment_id)
                if not comment:
                    self.error(404)
                    return
            else:
                comment = None

            # 4 cases:
            # 1 - New Post
            # 2 - Edit Existing Post
            # 3 - New Comment for existing post
            # 4 - Edit Comment for existing post
            #
            # Case 4 - Edit Comment for existing post
            if blog and comment:
                jinja_env.globals['cu_type'] = 'Edit Existing Comment'
                jinja_env.globals['new'] = False
                jinja_env.globals['ro_title'] = True
                params = dict(title=blog.title, content=comment.content, tags=blog.tags)
            # Case 3 - New Comment for existing post
            elif blog and iscomment:
                jinja_env.globals['cu_type'] = 'Create New Comment'
                jinja_env.globals['new'] = True
                jinja_env.globals['ro_title'] = True
                params = dict(title=blog.title, content='', tags=blog.tags)
            # Case 2 - Edit Existing Post
            elif blog:
                jinja_env.globals['cu_type'] = 'Edit Existing Post'
                jinja_env.globals['new'] = False
                jinja_env.globals['ro_title'] = False
                params = dict(title=blog.title, content=blog.content, tags=blog.tags)
            # Case 1 - New Post
            else:
                jinja_env.globals['cu_type'] = 'Author a New Post'
                jinja_env.globals['new'] = True
                jinja_env.globals['ro_title'] = False
                params = dict(title='', content='', tags='')

            self.render("cupost.html", **params)
        else:
            self.redirect("/signin?redirect=cupost")

    def post(self):
        logging.debug('CUPostPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=cupost')
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return

        jinja_env.globals['user'] = self.user.username

        post_id = self.request.get('post_id')
        entry = self.request.get('entry')
        comment_id = self.request.get('comment_id')
        cancel = self.request.get('cancel')
        if cancel:
            logging.debug('CUPostPage/post/Found cancel parameter of {}.'.format(cancel))
            if post_id:
                logging.debug('CUPostPage/post/Redirecting to /post/{}...'.format(post_id))
                self.redirect('/post/{}'.format(post_id))
                return
            else:
                logging.debug('CUPostPage/post/Redirecting to /...')
                self.redirect('/')
                return
        else:
            logging.debug('CUPostPage/post/No cancel parameter found.')

        logging.debug('CUPostPage/post/Made it passed cancel check.')
        params = dict(title=self.request.get('title'), content=self.request.get('content'),
                      tags=self.request.get('tags'), title_error='', content_error='',
                      tags_error='')

        # Options
        # Posts:
        # * New Post
        # * Edit Existing Post
        #
        # Comments:
        # * New Comment
        # * Edit Existing Comment
        #
        # Existing Blog Post - Validate
        if post_id:
            blog = valid_post(post_id)
            if not blog:
                self.error(404)
                return
            # Existing Comment - Validate
            if comment_id:
                # Look up comment_id:
                comment = valid_comment(post_id, comment_id)
                if not comment:
                    self.error(404)
                    return
                # Edit Existing Comment
                else:
                    comment.content = params['content']
                    comment.last_modified = datetime.datetime.now()
                    comment.put()
                    self.redirect('/post/{}'.format(post_id))
                    return
            # New Comment
            if entry == 'comment':
                # There's actually a comment
                if params['content']:
                    c = Comment(parent=blog.key(), content=params['content'],
                                author=self.user.username)
                    c.put()
                    self.redirect('/post/{}'.format(str(blog.key().id())))
                    return
                # No comment content
                else:
                    content_error = 'Please include some content in your comment.'
                    self.render("cupost.html", **params)
            # Edit Existing Post
            else:
                blog.title = params['title']
                blog.content = params['content']
                blog.tags = params['tags']
                blog.last_modified = datetime.datetime.now()
                blog.put()
                self.redirect('/post/{}'.format(post_id))
                return
        # New Blog Post
        elif params['title'] and params['content']:
            p = Blog(parent=Blog.pkey(), title=params['title'], author=self.user.username,
                     content=params['content'], tags=params['tags'])
            p.put()
            self.redirect('/post/{}'.format(str(p.key().id())))
            return
        # Blog Post missing parameters
        else:
            if not params['title']:
                title_error = 'Please include a title for your post.'
            if not params['content']:
                content_error = 'Please include some content in your post.'
            self.render("cupost.html", **params)

class PostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('PostPage/get/entered...')
        key = db.Key.from_path('Blog', int(post_id), parent=Blog.pkey())
        blog = db.get(key)

        if blog:
            likes, dislikes = post_votes(blog)
            comments = Comment.all().ancestor(blog.key()).order('created')

            # Setup environment:
            jinja_env.globals['likes'] = len(likes)
            jinja_env.globals['dislikes'] = len(dislikes)
            jinja_env.globals['pcomments'] = comments.count()
            jinja_env.globals['post_id'] = post_id
            jinja_env.globals['hide_ed'] = 'collapse'
            jinja_env.globals['hide_ld'] = 'collapse'
            jinja_env.globals['hide_ced'] = 'collapse'
        else:
            self.error(404)
            return
        if self.user:
            jinja_env.globals['userauth'] = True
            # Can I put this stuff in the initialize function?
            jinja_env.globals['user'] = self.user.username
            # Correct logic?
            if self.user.username in likes:
                jinja_env.globals['liked'] = self.user.username
                jinja_env.globals['disliked'] = None
            elif self.user.username in dislikes:
                jinja_env.globals['disliked'] = self.user.username
                jinja_env.globals['liked'] = None
        else:
            jinja_env.globals['userauth'] = False

        # Check for URL parameters - comment_id & entry action:
        comment_id = self.request.get('comment_id')
        if comment_id:
            ckey = db.Key.from_path('Comment', int(comment_id), parent=blog.key())
            comment = db.get(ckey)
        else:
            comment = None
        entry = self.request.get('entry')

        # All options require an authenticated user
        # Post Options
        # * Comment on post
        # * If author:
        # ** Edit post
        # ** Delete post
        # * If not author:
        # ** Like post
        # ** Dislike post
        #
        # Comment Options
        # * If author:
        # ** Edit comment
        # ** Delete comment
        #
        # Deal with comments first:
        # Authenticated user, valid comment (implies valid post), and action (entry) request:
        if self.user and comment and entry:
            # Is user comment author?
            if self.user.username == comment.author:
                if entry == 'edcomment':
                    self.redirect('/cupost?post_id={}&comment_id={}'.format(post_id, comment_id))
                    return
                elif entry == 'delcomment':
                    # Ideally prompt first with are you sure...
                    # Put a modal to do this in post.html but not sure how to integrate...
                    logging.debug('User {} deleted their comment created {} for post {}'
                                  '.'.format(self.user.username, comment.created, blog.title))
                    logging.debug('Note:  Blog id={}, Method Comment id={}, Passed Comment id={}'
                                  ''.format(blog.key().id(), comment.key().id(), comment_id))
                    db.delete(comment)
                    self.redirect('/post/{}'.format(post_id))
                    return
                else:
                    logging.debug('Invalid entry action - {} - ignoring.'.format(entry))
            # Not comment author - display error message:
            else:
                del jinja_env.globals['hide_ced']

        # Now deal with posts:
        # Authenticated user, valid blog if made it this far, and action (entry) request:
        elif self.user and entry:
            # Anyone can comment on a post
            if entry == 'comment':
                self.redirect('/cupost?post_id={}&entry=comment'.format(post_id))
                return

            # Is user post author?
            if self.user.username == blog.author:
                if entry == 'edpost':
                    self.redirect('/cupost?post_id={}'.format(post_id))
                    return
                elif entry == 'delpost':
                    # Ideally prompt first with are you sure...
                    # Put a modal to do this in post.html but not sure how to integrate...
                    logging.debug('User {} deleted their post {} last modified {}'
                                  '.'.format(self.user.username, blog.title, blog.last_modified))
                    db.delete(blog)
                    self.redirect('/')
                    return
                elif entry == 'like' or entry == 'dislike':
                    logging.debug('User {} tried to {} own post - permission '
                                  'denied.'.format(self.user.username, entry))
                    del jinja_env.globals['hide_ld']
                else:
                    logging.debug('Invalid entry action - {} - ignoring.'.format(entry))
            # Not the author - can only like/dislike post
            elif entry == 'like':
                likes.add(self.user.username)
                logging.debug('PostPage - {} {}s {}'.format(self.user.username, entry,
                              blog.title))
                blog.likes = set_pval(likes)
                dislikes.discard(self.user.username)
                blog.dislikes = set_pval(dislikes)
                jinja_env.globals['likes'] = len(likes)
                jinja_env.globals['dislikes'] = len(dislikes)
                jinja_env.globals['liked'] = self.user.username
                jinja_env.globals['disliked'] = None
                logging.debug('PostPage - {} {}d post, likes now = {}, dislikes now = {}'.format(
                              self.user.username, entry, likes, dislikes))
                blog.put()
                # Sleep for 100ms to give DB some time to write
                time.sleep(0.100)
                blog = db.get(key)
                likes, dislikes = post_votes(blog)
                logging.debug('PostPage - {} {}d post, after DB put, likes now = {}, dislikes '
                              'now = {}'.format(self.user.username, entry, likes, dislikes))
            elif entry == 'dislike':
                dislikes.add(self.user.username)
                logging.debug('PostPage - {} {}s {}'.format(self.user.username, entry,
                              blog.title))
                blog.dislikes = set_pval(dislikes)
                likes.discard(self.user.username)
                blog.likes = set_pval(likes)
                jinja_env.globals['likes'] = len(likes)
                jinja_env.globals['dislikes'] = len(dislikes)
                jinja_env.globals['disliked'] = self.user.username
                jinja_env.globals['liked'] = None
                logging.debug('PostPage - {} {}d post, likes now = {}, dislikes now = {}'.format(
                              self.user.username, entry, likes, dislikes))
                blog.put()
                # Sleep for 100ms to give DB some time to write
                blog = db.get(key)
                likes, dislikes = post_votes(blog)
                logging.debug('PostPage - {} {}d post, after DB put, likes now = {}, dislikes '
                              'now = {}'.format(self.user.username, entry, likes, dislikes))
            elif entry == 'edpost' or entry == 'delpost':
                logging.debug('User {} tried to edit/delete post by {} - permission '
                              'denied.'.format(self.user.username, blog.author))
                del jinja_env.globals['hide_ed']
            else:
                logging.debug('Invalid entry action - {} - ignoring.'.format(entry))
        # Tried to request an action (entry=...) but not authenticated - redirect to login
        elif entry:
            self.redirect('/signin?redirect=post/{}'.format(post_id))
            return

        self.render('post.html', title=blog.title, author=blog.author, content=blog.content,
                    tags=blog.tags, last_modified=blog.last_modified, comments=comments)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/cupost', CUPostPage),
                               ('/newpost', CUPostPage),
                               ('/editpost', CUPostPage),
                               (r'/post/(\d+)', PostPage),
                               ('/signin', SigninPage),
                               ('/signout', SignoutPage),
                               ('/signup', SignupPage),
                               ('/welcome', WelcomePage)], debug=True)

