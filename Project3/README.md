# Log Analysis Project w/ PostgreSQL
## Project 3

### Project Purpose
This project uses a PostgreSQL database.  The database is initialized with an authors, articles, and log tables.  These tables represent a fictitious newspaper site - the site's authors, their articles, and viewing statistics.  Using Python's DB-API, a script is created (news_stats.py) which queries the database to answer a list of questions.  The answer to the questions is output to the console.

### Installation and Requirements
* Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* Install [Vagrant](https://www.vagrantup.com/downloads.html)
* Clone [this](https://github.com/udacity/fullstack-nanodegree-vm) repository with git
* From the repo's vagrant directory, run:  `vagrant up`
* Create a news directory under the vagrant directory
* Download [the newsdata.zip database setup file](https://d17h27t6h515a5.cloudfront.net/topher/2016/August/57b5f748_newsdata/newsdata.zip) into the news directory
* Unzip the newsdata.zip file
* Setup the database:  `psql -d news -f newsdata.sql`
* Save the [news_stats.py](https://gist.github.com/sockduct/88a2058e6433b4b8c00c5e35bfaf3655) Python script into the news directory
* Connect to the Linux VM:  `vagrant ssh`
* From the Linux VM, change to the news directory:  `cd /vagrant/news`
* Run the script:  `python3 news_stats.py`
  * Note:  The script cannot be run directly because it has Windows-style line endings

### Project Layout
#### news_stats.py
* Simple Python script
  * Connects to database, defines queries, passes queries and formatting parameters to the get_query function which executes the queries, retrieves the results and outputs them to the console using the passed formatting parameters
  * The main function also determines the starting and ending dates of the logs and then iterates through each day to determine if an error threshold was crossed.  It the threshold is surpassed, this is displayed to the console.
  * Deviations from PEP8 - I use a line length of 100 characters instead of 80.  With modern computers and monitors, I find a width of 80 characters on the small side.

### License
MIT License

