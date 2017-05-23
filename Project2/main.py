from BlogHandler import BlogHandler
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
DATE_FMT = '%a %b %d, %Y at %H:%M:%S %z'

# Jinja template directory will be directory of this file + /templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Jinja setup and look for templates in template_dir
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               extensions=['jinja2.ext.loopcontrols'], autoescape=True)

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
        blogs = Blog.all().order('-created')
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
            self.redirect('/signin?redirect=cupost')

    def post(self):
        logging.debug('CUPostPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=cupost')
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
            self.render('cupost.html', **params)

class ViewPostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('NewPostPage/get/entered...')
        ### Is this the best way to approach this with the new 1:N model???
        key = db.Key.from_path('Blog', int(post_id), parent=Blog.pkey())
        blog = db.get(key)

        # Point of method is to view a blog post - if invalid ID, return 404 straight away
        if not blog:
            self.error(404)
            return
        else:
            likes, dislikes = post_votes(blog)
            comments = Comment.all().ancestor(blog.key()).order('created')

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
            jinja_env.globals['hide_ced'] = 'collapse'

        if self.user:
            jinja_env.globals['userauth'] = True
            ### Can I put this stuff in the initialize function???
            jinja_env.globals['user'] = self.user.username
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
            self.redirect('/signin?redirect=cupost')
        else:
            jinja_env.globals['user'] = self.user.username

            # Sanity check - look up post_id:
            blog = valid_post(post_id)
            if not blog:
                self.error(404)
                return

            jinja_env.globals['cu_type'] = 'Edit Existing Post'
            jinja_env.globals['new'] = False
            jinja_env.globals['ro_title'] = False
            params = dict(title=blog.title, content=blog.content, tags=blog.tags)

            self.render('cupost.html', **params)

    def post(self, post_id):
        logging.debug('EditPostPage/post/entered...')
        if not self.user:
            self.redirect('/signin?redirect=cupost')
            # Note - method execution continues without return after the redirect call, don't
            # forget!
            return

        jinja_env.globals['user'] = self.user.username
        blog = valid_post(post_id)

        cancel = self.request.get('cancel')
        if cancel:
            if blog:
                logging.debug('EditPostPage/post/Redirecting to /post/{}...'.format(post_id))
                self.redirect('/post/{}'.format(post_id))
                return
            else:
                logging.debug('CUPostPage/post/Redirecting to /...')
                self.redirect('/')
                return

        params = dict(title=self.request.get('title'), content=self.request.get('content'),
                      tags=self.request.get('tags'), title_error='', content_error='',
                      tags_error='')

        # Existing Blog Post - Validate
        if not blog:
            self.error(404)
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
            self.redirect('/post/{}'.format(post_id))

# Like/Dislike Post
class LikePostPage(BlogHandler):
    def get(self, post_id):
        logging.debug('(Dis)LikePostPage/get/entered...')
        # If path starts with like then like post
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
        key = db.Key.from_path('Blog', int(post_id), parent=Blog.pkey())
        blog = db.get(key)

        # Initialize likes/dislikes
        likes, dislikes = post_votes(blog)

        # If invalid blog, deal with straight away...
        if not blog:
            self.error(404)
            return

        # Must be authenticated
        if not self.user:
            self.redirect('/signin?redirect={}post/{}'.format(likestr, post_id))
            return
        else:
            # Is user post author?  Can't like/dislike own post!
            if self.user.username == blog.author:
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

                logging.debug('LikePostPage - {} {}s {}'.format(self.user.username, likestr, blog.title))
                blog.likes = set_pval(likes)
                blog.dislikes = set_pval(dislikes)
                logging.debug('LikePostPage - {} {}d post, likes now = {}, dislikes now = {}'.format(
                              self.user.username, likestr, likes, dislikes))
                blog.put()
                # Sleep for 100ms to give DB some time to write
                time.sleep(0.100)
                blog = db.get(key)
                likes, dislikes = post_votes(blog)
                logging.debug('PostPage - {} {}d post, after DB put, likes now = {}, dislikes '
                              'now = {}'.format(self.user.username, entry, likes, dislikes))

        self.redirect('/post/{}'.format(post_id))

# Create Comment regarding Post
class NewCommentPage(BlogHandler):
    def get(self, post_id):
        logging.debug('NewCommentPage/get/entered...')

        # Must be authenticated or redirect straight away...
        if not self.user:
            self.redirect('/signin?redirect=newcomment/{}'.format(post_id))
        else:
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

            self.render('cupost.html', **params)

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
                    self.render('cupost.html', **params)
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
            self.render('cupost.html', **params)

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

            self.render('cupost.html', **params)
        else:
            self.redirect('/signin?redirect=cupost')

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
                    self.render('cupost.html', **params)
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
            self.render('cupost.html', **params)


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/newpost', NewPostPage),
                               (r'/post/(\d+)', ViewPostPage),
                               (r'/editpost/(\d+)', EditPostPage),
                               (r'/likepost/(\d+)', LikePostPage),
                               (r'/dislikepost/(\d+)', LikePostPage),
                               (r'/newcomment/(\d+)', NewCommentPage),
                               (r'/editcomment/(\d+)&(\d+)', EditCommentPage),

                               ('/cupost', CUPostPage),

                               ('/signin', SigninPage),
                               ('/signout', SignoutPage),
                               ('/signup', SignupPage),
                               ('/welcome', WelcomePage)], debug=True)

