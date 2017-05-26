# Google App Engine w/ Python App Project
## Multi User Blog (Project 2)

### Project Purpose
This project utilizes the Google App Engine Framework for Python to create a multi-user blog web site.  This is conceptually a simplied version of something like medium.com.  The main page displays all blogs created on the site.  Users wishing to create blog entries must register.  Each blog can be commented on by any registerd user.  In addition, anyone other than the blog author may like/dislike the blog entry.  Author's may delete their blogs or comments.

### Installation and Requirements
* Clone or download the project directory
* [Python 2.7](https://www.python.org/downloads/)
* [The Google App Engine SDK for Python](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python)
* [Google App Engine Account](https://console.cloud.google.com/appengine/)
* [Create/Use a unique project name on the Google Developer Console](https://console.cloud.google.com/)
* Initialize the local environment to use your GAE Account and Project (See [App Engine Quickstart](https://cloud.google.com/appengine/docs/python/quickstart) for an example)
* Deploy the project:  `gcloud app deploy`
* Open the project:  `gcloud app browse`
Note:  This project uses Jinja2 as a templating engine - this is built-in to the GAE Python Platform

### Project Layout
#### Source files (not used by web site)
* bootstrap - Bootstrap framework source files (CSS/Fonts/JavaScript)
* font-awesome-4.7.0 - Icon fonts
* ./BlogHandler.py - Class definition (not actually used)

#### Code files (used by web site)
* entities - Google App Engine Datastore Entities (class definitions - see below)
* static - CSS/Fonts/Image/JavaScript files used by site
* templates - Jinja2 templates used by site
* ./app.yaml - GAE initialization file
* ./environment.cfg - secret key
* ./index.yaml - GAE state file (not critical)
* ./main.py - Main Program
* ./README.md - this file
* ./utils.py - Utility functions (used by Main and Entities)

##### GAE Datastore Entities (entities directory)
* User - Represents a user account
* Blog - Represents a user post, linked to respective user
* Comment - Represents a user comment on a post, linked to respective post

Path | Main Methods
-----|--------------
/ | MainPage, Landing/default page - displays all posts 
/newpost | NewPostPage, Create a new post (must be authenticated)
/viewpost/[0-9]+ | ViewPostPage, View passed post
/editpost/[0-9]+ | EditPostPage, Edit existing (passed) post (must be authenticated and post author)
/delpost/[0-9]+ | DelPostPage, Delete existing (passed) post (must be authenticated and post author)
/likepost/[0-9]+ | LikePostPage, Like existing (passed) post (must be authenticated and cannot be post author)
/dislikepost/[0-9]+ | LikePostPage, Dislike existing (passed) post (must be authenticated and cannot be post author)
/newcomment/[0-9]+ | NewCommentPage, Create a comment for an existing post (must be authenticated)
/editcomment/[0-9]+&[0-9]+ | EditCommentPage, Edit an existing post comment (must be authenticated and comment author)
/delcomment/[0-9]+&[0-9]+ | DelCommentPage, Delete an existing post comment (must be authenticated and comment author)
/post/[0-9]+ | PostPage, View an individual post by id, links to edit, delete, like/dislike or comment on post
/signin | SigninPage, Login page for users with an account
/signout | SignoutPage, Logout page for authenticated users
/signup | SignupPage, Register for an account
/welcome | WelcomePage, Greet authenticated users

Note:  For pages that require authentication, if the user isn't authenticated he will be redirected to /signin

### License
MIT License

