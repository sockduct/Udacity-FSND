# Google App Engine w/ Python App Project
## Multi User Blog (Project 2)

##### GAE Datastore Entities
* User - Represents a user account
* Blog - Represents a user post
* Comment - Represents a user comment on a post, linked to respective post

Path | Main Methods
-----|--------------
/ | MainPage, Landing/default page - displays all posts 
/cupost|newpost|editpost | CUPostPage, Create or Update posts
/post/[0-9]+ | PostPage, View an individual post by id, links to edit, delete, like/dislike or comment on post
/signin | SigninPage, Login page for users with an account
/signout | SignoutPage, Logout page for authenticated users
/signup | SignupPage, Register for an account
/welcome | WelcomePage, Greet authenticated users

