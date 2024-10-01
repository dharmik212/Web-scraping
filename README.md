# Web-scraping
This Python-based web scraper extracts historical State of the Union speeches from the web and stores them in a SQL Server database. The project automates the process of downloading speeches, saving them as text files, and inserting their content into a relational database for easy querying and analysis.

# Features
Scrapes State of the Union addresses from a public website.
Extracts the President’s name, date of the address, and full speech text.
Saves speeches as individual text files and appends them to a combined file.
Stores speech data (president, date, text, etc.) in a SQL Server database.
Logs broken links and handles errors gracefully.

# Prerequisites
To run this project, you will need the following installed on your system:
Python 3.x
requests, lxml, pyodbc libraries (install via pip install -r requirements.txt)
SQL Server (locally configured)
