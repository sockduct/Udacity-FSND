import datetime
# Can cause circular dependenices
# from entities import User, Blog, Comment
import entities
from google.appengine.ext import db
import jinja2
import logging
import os
import time
# Can cause circular dependenices
# from utils import *
import utils
import webapp2

####################################################################################################
# To Do
#===================================================================================================
# * Add delay after deleting post (maybe after deleting comment too) so it doesn't temporarily show
#   up when user is directed back to landing page
#
####################################################################################################
# Constants
DATE_FMT = '%a %b %d, %Y at %H:%M:%S %z'

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               extensions=['jinja2.ext.loopcontrols'], autoescape=True)

# Note - tried to put this in its own file, but then not sure how to pass jinja2 environment
# variables
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
        sec_cval = utils.make_sec_val(cval)
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
        #elif utils.chk_sec_val(cval):
        #    logging.debug('Successfully read and validated userid cookie')
        #else:
        #    logging.debug('Validation of userid cookie failed')
        #t1 = cval and utils.chk_sec_val(cval)
        #t2 = utils.chk_sec_val(cval)
        #logging.debug('{} and {} = {}'.format(cval, t2, t1))
        return cval and utils.chk_sec_val(cval)

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
            #t1 = entities.User.by_id(int(uid))
            #logging.debug('User.by_id({}) = {}'.format(uid, t1))
            #t2 = uid and t1
            #logging.debug('uid and User.by_id({}) = {}'.format(uid, t2))
        self.user = uid and entities.User.by_id(int(uid))

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

        utils.check_user_info(params)

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
        user = entities.User.create(**params)
        self.login(user, params['host'], params['auth_cookie'])
        self.redirect('/welcome')

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

        utils.check_user_info(params)

        if params['have_error']:
            logging.debug('SigninPage - authentication error')
            params['password'] = ''
            self.render('signin.html', **params)
        # Acceptable credentials - check if valid
        else:
            logging.debug('SigninPage - attempting login...')
            user = entities.User.login(username, password)
            if user:
                self.login(user, host, auth_cookie)
                self.render('welcome.html', username=username)
            else:
                # Invalid username and/or password
                params['password'] = ''
                params['auth_error'] = 'Invalid username and/or password'
                self.render('signin.html', **params)

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
        blogs = entities.Blog.all().order('-created')
        jinja_env.globals['now'] = datetime.datetime.now().strftime(DATE_FMT)
        jinja_env.globals['bcount'] = blogs.count()
        if self.user:
            jinja_env.globals['userauth'] = True
            jinja_env.globals['user'] = self.user.username
        else:
            jinja_env.globals['userauth'] = False
        self.render('landing.html', blogs=blogs)

# Create a New Post
class NewPostPage(BlogHandler):
    def get(self):
        logging.debug('NewPostPage/get/entered...')
        if self.user:
            jinja_env.globals['user'] = self.user.username

            # Use same underlying template or change?  Think about - but perhaps change...
            jinja_env.globals['cu_type'] = 'Author a New Post'
            jinja_env.globals['new'] = True
            jinja_env.globals['ro_title'] = False
            params = dict(title='', content='', tags='')

            self.render('cupost.html', **params)
        else:
            self.redirect('/signin?redirect=newpost')

    def post(self):
        logging.debug('NewPostPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=newpost')
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return

        jinja_env.globals['user'] = self.user.username

        cancel = self.request.get('cancel')
        if cancel:
            logging.debug('NewPostPage/post/Found cancel parameter of {}.'.format(cancel))
            logging.debug('NewPostPage/post/Redirecting to /...')
            self.redirect('/')
            return

        params = dict(title=self.request.get('title'), content=self.request.get('content'),
                      tags=self.request.get('tags'), title_error='', content_error='',
                      tags_error='')

        # New Blog Post - Validation
        if params['title'] and params['content']:
            p = entities.Blog(parent=entities.Blog.pkey(), title=params['title'], author=self.user.username,
                     content=params['content'], tags=params['tags'])
            p.put()
            self.redirect('/viewpost/{}'.format(str(p.key().id())))
            return
        # Blog Post missing parameters
        else:
            if not params['title']:
                title_error = 'Please include a title for your post.'
            if not params['content']:
                content_error = 'Please include some content in your post.'
            self.render('cupost.html', **params)

class ViewPostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('ViewPostPage/get/entered...')
        ### Is this the best way to approach this with the new 1:N model???
        key = db.Key.from_path('Blog', int(post_id), parent=entities.Blog.pkey())
        blog = db.get(key)

        # Point of method is to view a blog post - if invalid ID, return 404 straight away
        if not blog:
            self.error(404)
            return
        else:
            likes, dislikes = utils.post_votes(blog)
            comments = entities.Comment.all().ancestor(blog.key()).order('created')

            # Setup environment:
            jinja_env.globals['likes'] = len(likes)
            jinja_env.globals['dislikes'] = len(dislikes)
            jinja_env.globals['pcomments'] = comments.count()
            ### Needed just for viewing post???
            jinja_env.globals['post_id'] = post_id
            ### Probably want to leave in here - no point in routing to another method if user
            # doesn't have permission
            ### However, best way is probably to handle this with JavaScript code and not here...
            jinja_env.globals['hide_ed'] = 'collapse'
            jinja_env.globals['hide_ld'] = 'collapse'

        if self.user:
            jinja_env.globals['userauth'] = True
            ### Can I put this stuff in the initialize function???
            jinja_env.globals['user'] = self.user.username
            # Check for errors from like/dislike method:
            lstat = self.request.get('lstat')
            if lstat and int(lstat) == 1:
                del jinja_env.globals['hide_ld']
            # Check for errors from editpost/delpost methods:
            epstat = self.request.get('epstat')
            dpstat = self.request.get('dpstat')
            if (epstat and int(epstat) == 1) or (dpstat and int(dpstat) == 1):
                del jinja_env.globals['hide_ed']
            # Check for errors from editcomment/delcomment methods:
            ecstat = self.request.get('ecstat')
            dcstat = self.request.get('dcstat')
            cid = self.request.get('cid')
            if (ecstat and int(ecstat) == 1) or (dcstat and int(dcstat) == 1):
                jinja_env.globals['ced'] = True
                jinja_env.globals['cid'] = cid
            ### Correct logic???
            if self.user.username in likes:
                jinja_env.globals['liked'] = self.user.username
                jinja_env.globals['disliked'] = None
            elif self.user.username in dislikes:
                jinja_env.globals['disliked'] = self.user.username
                jinja_env.globals['liked'] = None
        else:
            jinja_env.globals['userauth'] = False

        self.render('post.html', title=blog.title, author=blog.author, content=blog.content,
                    tags=blog.tags, last_modified=blog.last_modified, comments=comments)

# Create or Update Post
class EditPostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('EditPostPage/get/entered...')
        # Point of method is to edit post - if user not authenticated deal with straight away...
        if not self.user:
            self.redirect('/signin?redirect=editpost/{}'.format(post_id))
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity check - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != blog.author:
                logging.debug("User {} tried to edit {}'s post - permission denied.".format(
                              self.user.username, blog.author))
                self.redirect('/viewpost/{}?epstat=1'.format(post_id))
                return

            jinja_env.globals['cu_type'] = 'Edit Existing Post'
            jinja_env.globals['new'] = False
            jinja_env.globals['ro_title'] = False
            params = dict(title=blog.title, content=blog.content, tags=blog.tags)

            self.render('cupost.html', **params)

    def post(self, post_id):
        logging.debug('EditPostPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=editpost/{}'.format(post_id))
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return
        else:
            jinja_env.globals['user'] = self.user.username
            blog = utils.valid_post(post_id)

            cancel = self.request.get('cancel')
            if cancel:
                if blog:
                    logging.debug('EditPostPage/post/Redirecting to /post/{}...'.format(post_id))
                    self.redirect('/viewpost/{}'.format(post_id))
                    return
                else:
                    logging.debug('EditPostPage/post/Redirecting to /...')
                    self.redirect('/')
                    return

            params = dict(title=self.request.get('title'), content=self.request.get('content'),
                          tags=self.request.get('tags'), title_error='', content_error='',
                          tags_error='')

            # Existing Blog Post - Validate
            if not blog:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != blog.author:
                logging.debug("User {} tried to edit {}'s post - permission denied.".format(
                              self.user.username, blog.author))
                self.redirect('/viewpost/{}?epstat=1'.format(post_id))
                return

            # Edit Existing Post
            blog.title = params['title']
            blog.content = params['content']
            blog.tags = params['tags']
            blog.last_modified = datetime.datetime.now()

            # Sanity check - Blog Post missing parameters?
            have_errors = False
            if not params['title']:
                title_error = 'Please include a title for your post.'
                have_errors = True
            if not params['content']:
                content_error = 'Please include some content in your post.'
                have_errors = True
            if have_errors:
                self.render('cupost.html', **params)
            else:
                blog.put()
                ### Need write delay here???
                self.redirect('/viewpost/{}'.format(post_id))

# Create or Update Post
class DelPostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('DelPostPage/get/entered...')
        # Point of method is to delete post - if user not authenticated deal with straight away...
        if not self.user:
            self.redirect('/signin?redirect=delpost/{}'.format(post_id))
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity check - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != blog.author:
                logging.debug("User {} tried to delete {}'s post - permission denied.".format(
                              self.user.username, blog.author))
                self.redirect('/viewpost/{}?dpstat=1'.format(post_id))
                return

            jinja_env.globals['cu_type'] = 'Delete Existing Post'
            jinja_env.globals['new'] = False
            jinja_env.globals['ro_title'] = True
            jinja_env.globals['ro_content'] = True
            params = dict(title=blog.title, content=blog.content, tags=blog.tags)

            self.render('cupost.html', **params)

    def post(self, post_id):
        logging.debug('DelPostPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=delpost/{}'.format(post_id))
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return
        else:
            jinja_env.globals['user'] = self.user.username
            blog = utils.valid_post(post_id)

            cancel = self.request.get('cancel')
            if cancel:
                if blog:
                    logging.debug('DelPostPage/post/Redirecting to /post/{}...'.format(post_id))
                    self.redirect('/viewpost/{}'.format(post_id))
                    return
                else:
                    logging.debug('DelPostPage/post/Redirecting to /...')
                    self.redirect('/')
                    return

            # Existing Blog Post - Validate
            if not blog:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != blog.author:
                logging.debug("User {} tried to delete {}'s post - permission denied.".format(
                              self.user.username, blog.author))
                self.redirect('/viewpost/{}?dpstat=1'.format(post_id))
                return

            # If user didn't cancel then delete post
            db.delete(blog)
            ### Need small delay to allow DB to purge the post...
            time.sleep(0.100)
            self.redirect('/')

# Like/Dislike Post
class LikePostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('(Dis)LikePostPage/get/entered...')
        # If path starts with like then like post
        path = self.request.path
        if str(path).startswith('/like'):
            like = True
            likestr = 'like'
        # If path starts with dislike then dislike post
        elif str(path).startswith('/dislike'):
            like = False
            likestr = 'dislike'
        # Else error
        else:
            raise ValueError('Unexpected URL path of {} - expected either "/like..." or '
                             '"/dislike..."'.format(path))

        # Get blog
        key = db.Key.from_path('Blog', int(post_id), parent=entities.Blog.pkey())
        blog = db.get(key)

        # Initialize likes/dislikes
        likes, dislikes = utils.post_votes(blog)

        # If invalid blog, deal with straight away...
        if not blog:
            self.error(404)
            return

        # Must be authenticated
        if not self.user:
            self.redirect('/signin?redirect={}post/{}'.format(likestr, post_id))
            return
        else:
            # Status: -1=error, 0=success, 1=denied, 2=initial/unknown
            status = 2
            # Is user post author?  Can't like/dislike own post!
            if self.user.username == blog.author:
                status = 1
                logging.debug('User {} tried to {} own post - permission denied.'.format(
                              self.user.username, likestr))
            # Not the author - can only like/dislike post
            #elif like:
            else:
                if like:
                    likes.add(self.user.username)
                    dislikes.discard(self.user.username)
                else:
                    dislikes.add(self.user.username)
                    likes.discard(self.user.username)

                status = 0
                logging.debug('LikePostPage - {} {}s {}'.format(self.user.username, likestr, blog.title))
                blog.likes = utils.set_pval(likes)
                blog.dislikes = utils.set_pval(dislikes)
                logging.debug('LikePostPage - {} {}d post, likes now = {}, dislikes now = {}'.format(
                              self.user.username, likestr, likes, dislikes))
                blog.put()
                # Sleep for 100ms to give DB some time to write
                time.sleep(0.100)
                blog = db.get(key)
                likes, dislikes = utils.post_votes(blog)
                logging.debug('LikePostPage - {} {}d post, after DB put, likes now = {}, dislikes '
                              'now = {}'.format(self.user.username, likestr, likes, dislikes))

        self.redirect('/viewpost/{}?lstat={}'.format(post_id, status))

# Create Comment regarding Post
class NewCommentPage(BlogHandler):
    def get(self, post_id):
        logging.debug('NewCommentPage/get/entered...')

        # Must be authenticated or redirect straight away...
        if not self.user:
            self.redirect('/signin?redirect=newcomment/{}'.format(post_id))
            return
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity checks - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return

            jinja_env.globals['cu_type'] = 'Create New Comment'
            jinja_env.globals['new'] = True
            jinja_env.globals['ro_title'] = True
            params = dict(title=blog.title, content='', tags=blog.tags)

            self.render('cupost.html', **params)

    def post(self, post_id):
        logging.debug('NewCommentPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=newcomment/{}'.format(post_id))
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity checks - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return

            # Shouldn't need
            # post_id = self.request.get('post_id')

            cancel = self.request.get('cancel')
            if cancel:
                logging.debug('NewCommentPage/post/Found cancel parameter of {}.'.format(cancel))
                if post_id:
                    logging.debug('NewPostPage/post/Redirecting to /post/{}...'.format(post_id))
                    self.redirect('/viewpost/{}'.format(post_id))
                    return
                else:
                    logging.debug('NewCommentPage/post/Redirecting to /...')
                    self.redirect('/')
                    return

            params = dict(title=self.request.get('title'), content=self.request.get('content'),
                          tags=self.request.get('tags'), title_error='', content_error='',
                          tags_error='')

            # New Comment - Check there's actually a comment
            if params['content']:
                c = entities.Comment(parent=blog.key(), content=params['content'],
                            author=self.user.username)
                c.put()
                self.redirect('/viewpost/{}'.format(str(blog.key().id())))
                return
            # No comment content
            else:
                content_error = 'Please include some content in your comment.'
                self.render('cupost.html', **params)

# Edit Comment regarding Post
class EditCommentPage(BlogHandler):
    def get(self, post_id, comment_id):
        logging.debug('EditCommentPage/get/entered...')

        # If user not authenticated, deal with straight away...
        if not self.user:
            self.redirect('/signin?redirect=editcomment/{}&{}'.format(post_id, comment_id))
            return
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity checks - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return
            ### valid_comment might need some work on parent path...
            ### Look up comment_id:
            comment = utils.valid_comment(post_id, comment_id)
            if not comment:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != comment.author:
                logging.debug("User {} tried to edit {}'s comment - permission denied.".format(
                              self.user.username, comment.author))
                self.redirect('/viewpost/{}?ecstat=1&cid={}'.format(post_id, comment_id))
                return

            jinja_env.globals['cu_type'] = 'Edit Existing Comment'
            jinja_env.globals['new'] = False
            jinja_env.globals['ro_title'] = True
            params = dict(title=blog.title, content=comment.content, tags=blog.tags)

            self.render('cupost.html', **params)

    def post(self, post_id, comment_id):
        logging.debug('EditCommentPage/post/entered...')

        if not self.user:
            self.redirect('/signin?redirect=editcomment/{}&{}'.format(post_id, comment_id))
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity checks - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return
            ### valid_comment might need some work on parent path...
            ### Look up comment_id:
            comment = utils.valid_comment(post_id, comment_id)
            if not comment:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != comment.author:
                logging.debug("User {} tried to edit {}'s comment - permission denied.".format(
                              self.user.username, comment.author))
                self.redirect('/viewpost/{}?ecstat=1&cid={}'.format(post_id, comment_id))
                return

            cancel = self.request.get('cancel')
            if cancel:
                if post_id:
                    logging.debug('EditCommentPage/post/Redirecting to /post/{}...'.format(post_id))
                    self.redirect('/viewpost/{}'.format(post_id))
                    return
                else:
                    logging.debug('EditCommentPage/post/Redirecting to /...')
                    self.redirect('/')
                    return

            params = dict(title=self.request.get('title'), content=self.request.get('content'),
                          tags=self.request.get('tags'), title_error='', content_error='',
                          tags_error='')

            # Check there's actually a comment
            if params['content']:
                comment.content = params['content']
                comment.last_modified = datetime.datetime.now()
                comment.put()
                self.redirect('/viewpost/{}'.format(post_id))
                return
            # No comment content
            else:
                content_error = 'Please include some content in your comment.'
                self.render('cupost.html', **params)

# Delete Comment regarding Post
class DelCommentPage(BlogHandler):
    def get(self, post_id, comment_id):
        logging.debug('DelCommentPage/get/entered...')

        # If user not authenticated, deal with straight away...
        if not self.user:
            self.redirect('/signin?redirect=delcomment/{}&{}'.format(post_id, comment_id))
            return
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity checks - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return
            ### valid_comment might need some work on parent path...
            ### Look up comment_id:
            comment = utils.valid_comment(post_id, comment_id)
            if not comment:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != comment.author:
                logging.debug("User {} tried to delete {}'s comment - permission denied.".format(
                              self.user.username, comment.author))
                self.redirect('/viewpost/{}?dcstat=1&cid={}'.format(post_id, comment_id))
                return

            jinja_env.globals['cu_type'] = 'Delete Existing Comment'
            jinja_env.globals['new'] = False
            jinja_env.globals['ro_title'] = True
            jinja_env.globals['ro_content'] = True
            params = dict(title=blog.title, content=comment.content, tags=blog.tags)

            self.render('cupost.html', **params)

    def post(self, post_id, comment_id):
        logging.debug('DelCommentPage/post/entered...')

        if not self.user:
            self.redirect('/signin?redirect=delcomment/{}&{}'.format(post_id, comment_id))
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity checks - look up post_id:
            blog = utils.valid_post(post_id)
            if not blog:
                self.error(404)
                return
            ### valid_comment might need some work on parent path...
            ### Look up comment_id:
            comment = utils.valid_comment(post_id, comment_id)
            if not comment:
                self.error(404)
                return

            # Authorization check:
            if self.user.username != comment.author:
                logging.debug("User {} tried to delete {}'s comment - permission denied.".format(
                              self.user.username, comment.author))
                self.redirect('/viewpost/{}?dcstat=1&cid={}'.format(post_id, comment_id))
                return

            cancel = self.request.get('cancel')
            if cancel:
                if post_id:
                    logging.debug('DelCommentPage/post/Redirecting to /post/{}...'.format(post_id))
                    self.redirect('/viewpost/{}'.format(post_id))
                    return
                else:
                    logging.debug('DelCommentPage/post/Redirecting to /...')
                    self.redirect('/')
                    return

            # If user didn't cancel, then delete comment
            db.delete(comment)
            self.redirect('/viewpost/{}'.format(post_id))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPostPage),
                               (r'/viewpost/(\d+)', ViewPostPage),
                               (r'/editpost/(\d+)', EditPostPage),
                               (r'/delpost/(\d+)', DelPostPage),
                               (r'/likepost/(\d+)', LikePostPage),
                               (r'/dislikepost/(\d+)', LikePostPage),
                               (r'/newcomment/(\d+)', NewCommentPage),
                               (r'/editcomment/(\d+)&(\d+)', EditCommentPage),
                               (r'/delcomment/(\d+)&(\d+)', DelCommentPage),
                               ('/signin', SigninPage),
                               ('/signout', SignoutPage),
                               ('/signup', SignupPage),
                               ('/welcome', WelcomePage)], debug=True)

