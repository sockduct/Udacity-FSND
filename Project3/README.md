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
* Using DB-API, answer following questions as defined in project:
  1. What are the most popular three articles of all time?
  2. Who are the most popular article authors of all time?
  3. On which days did more than 1% of requests lead to errors?
* Program layout:
  * fetch_query - connect to database, query with passed parameter, fetch and return results
  * print_top_articles - answer question one (houses single SQL query to answer)
  * print_top_authors - answer question two (houses single SQL query to answer)
  * print_daily_errors - answer question three (houses single SQL query to answer question)
  * format_col - helper function for print_results, determines column formatting and width(s)
  * print_results - helper function for print... functions from above which answer the questions, using passed parameter formats header row, header/data separator, and data rows
  * main - if program run directly, execute print... functions from above which answer questions
* Program notes:
  * Deviations from PEP8 - I use a line length of 100 characters instead of 80.  With modern computers and monitors, I find a width of 80 characters on the small side.

### Example Project Output
* output.txt

### License
MIT License

