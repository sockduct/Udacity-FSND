# [Udacity](https://www.udacity.com/) [Full Stack Web Developer NanoDegree](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004) Projects

* [Project 1 - x](Project1)

=======

# Linux Server (Hosting [Item Catalog Application](https://github.com/sockduct/FSND-Project-4/))
## Project 6

### Project Purpose and Notes
This project takes the web application created in Project 4 and hosts it on an AWS Lightsail VPS.  The purpose is to setup the created web application on a hosted Linux server.  As part of this solution, the server is locked down and secured.  The integral web app backend database (PostgreSQL) is also setup on the server.

##### Review Details:
* Instance IP address:  34.201.23.222
* Instance SSH port:  2200
* Web App URL:  http://34.201.23.222
* Installed packages and configuration changes - please see installation and requirements below
* Resources used to complete this project:
  * [Udacity Configuring Linux Web Servers Course](https://www.udacity.com/course/configuring-linux-web-servers--ud299)
  * [PostgreSQL Documentation](https://www.postgresql.org/docs/9.5/static/index.html)
  * [Flask Documentation](http://flask.pocoo.org/docs/0.12/)
  * StackOverflow - mainly to figure out where to look in the docs for PostgreSQL (authentication with UNIX Domain Sockets) and Flask (how to connect my app into Apache through WSGI)
  * [Learning Python, 5th Edition](https://www.safaribooksonline.com/library/view/learning-python-5th/9781449355722/) - good general resource for understanding Python at a deep level, especially helpful for understanding scope and imports

##### Notes:
* The database has been changed to a local PostgreSQL instance (from a simple SQLite file)
* Connectivity between the web app and the database is via UNIX Domain Sockets using local database authentication (md5)
* An optional database_setup.py script is included to populate the database with example sports items
* For additional details, please see [the Project 4 README](https://github.com/sockduct/FSND-Project-4/blob/master/README.md)

### Installation and Requirements
* Setup an [AWS Lightsail VPS](https://amazonlightsail.com/) running Ubuntu 16.04 - the smallest VPS is fine
* In the [Lightsail Console](https://lightsail.aws.amazon.com/ls/webapp/home/resources) add TCP/2200 to the allowed ports in the firewall
* Install the following Ubuntu packages:
  ```
  sudo apt-get update
  sudo apt-get install apache2 libapache2-mod-wsgi postgresql python-httplib2 python-requests python-flask python-flask-httpauth python-oauth2client python-sqlalchemy python-itsdangerous python-passlib python-redis python-psycopg2
  ```
* Not available as a distro package, install directly from Python Package Index ([PyPI](https://pypi.python.org/))
  `sudo pip install Flask-Uploads`
* Update the Ubuntu Server:
  ```
  sudo apt-get update
  sudo apt-get upgrade
  sudo apt-get autoremove
  ```
* After the package upgrade is completed, the server may require a reboot.  If so, reboot at this point:
  `sudo reboot`
* From /var/www/html, Clone [this](https://github.com/sockduct/FSND-Project-6) repository to catalog:
  `sudo git clone https://github.com/sockduct/FSND-Project-6 catalog`
* Create/supply the following files in the catalog directory:
  * app_secret.json - used to store flask app secret key used to secure client sessions
  * client_secret_google.json - used for Google OAUTH
* Update the ssh config (/etc/ssh/sshd_config):
  * Comment out:  Port 22
  * Add:  Port 2200
  * Change:  PermitRootLogin no
  * Change:  PasswordAuthentication no
  * Restart ssh after config change:  `sudo service ssh restart`
* Setup the server firewall using ufw:
  ```
  sudo ufw status
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow 2200/tcp
  sudo ufw allow www
  sudo ufw allow ntp
  sudo ufw enable
  sudo ufw status
  ```
* Configure Apache on the server:
  * Create catalogapp.wsgi in /var/www/html:
      ```
      import sys
      sys.path.insert(0, '/var/www/html/catalog')

      import views as application
      ```
  * Edit /etc/apache2/sites-enabled/000-default.conf:
    * Add before </VirtualHost>:  WSGIScriptAlias / /var/www/html/catalogapp.wsgi
  * After changing above, restart Apache:
    `sudo apache2ctl restart`
* Configure PostgreSQL database on server:
  * Create user "catalog":  `sudo -u postgres createuser -D -E -P -R -S catalog`
    * Note:  If you change the password from what's used in the Python scripts, then all relevant scripts must be updated
  * Create database "catalog" owned by user "catalog":  `sudo -u postgres createdb -O catalog catalog`
  * Allow encrypted username/password authentication using UNIX Domain Sockets for communication between the web app and the database
    * Add following auth entry to /etc/postgresql/9.5/main/pg_hba.conf:
      * Before this entry:
        `local   all             all                                     peer`
      * Add the following:
        ```
        # "local" is for Unix domain socket connections only
        local   catalog         catalog                                 md5
        ```
  * Re-read config files (use SIGHUP):
    * Assuming current PostgreSQL version is 9.5 and cluster name is main:
      `pg_ctlcluster 9.5 main reload`

### Project Requirements/Solution Layout
* The project implements a JSON endpoint that serves the same information as displayed in the HTML endpoints for an arbitrary item in the catalog
* README (this file)
* This uses the web app created in Project 4, please see [that README](https://github.com/sockduct/FSND-Project-4/blob/master/README.md) for a complete overview of that project

### License
[MIT License](license.txt)

