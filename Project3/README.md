# Log Analysis Project with PostgreSQL
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

### Project Requirements
* Using DB-API, answer following questions - each with a single SQL query:
  1. What are the most popular three articles of all time?
  2. Who are the most popular article authors of all time?
  3. On which days did more than 1% of requests lead to errors?

### Project Solution Layout
#### news_stats.py
* Program layout:
  * fetch_query - connect to database, query with passed parameter, fetch and return results
  * print_top_articles - answer question one (houses single SQL query to answer), one optional parameter specifying the maximum number of desired results (e.g., if you pass 2, it will only show you the top 2 articles)
  * print_top_authors - answer question two (houses single SQL query to answer), one optional parameter specifying the maximum number of desired results (e.g., if you pass 3, it will only show you the top 3 authors)
  * print_daily_errors - answer question three (houses single SQL query to answer question), one optional parameter specifying the minimum error threshold (e.g., if you pass 2, it will only show you days where the percentage of errors is > 2%; can use integers {1, 2, 5} or floating points values {0.35, 1.7, 3.95})
  * print_daily_stats - extra function which shows daily statistics including total number of page views/requests, number of errors and error percentage for all records/days in the database
  * format_col - helper function for print_results, determines column formatting and width(s)
  * print_results - helper function for print... functions from above which answer the questions, using passed parameter formats header row, header/data separator, and data rows
  * main - if program run directly, execute print... functions from above which answer questions, if optional "test" argument passed then use alternate function invocation to test function's other branches

### Example Project Output
* [output.txt](output.txt)

### License
[MIT License](LICENSE)

