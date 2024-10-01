# Required Libraries
import requests
from lxml import html
from lxml import etree
import os
import pyodbc
from urllib.parse import urljoin
from datetime import datetime

# Main program starts here
def main():
    """A web scraper that extracts State of the Union address speeches and stores them in a SQL Server table."""
    
    # setup SQL Server connection
    server = r'DHARMIK\SQLSERVER2022'
    database = 'STATE_UNION_ADDRESSES'
    table = 'ADDRESS_TABLE'
    main_url = 'https://www.infoplease.com'
    speeches_url = 'https://www.infoplease.com/primary-sources/government/presidential-speeches/state-union-addresses'

    # Connect to SQL Server and create the database and table
    cursor = connect_to_sql_server(server, database, table)

    # Get main page content to parse
    page = requests.get(speeches_url)
    tree = html.fromstring(page.content)
    html_etree = etree.ElementTree(tree)

    # Create output directory for speech text files
    output_directory = os.path.join(os.getcwd(), 'SpeechFiles')
    os.makedirs(output_directory, exist_ok=True)

    # Create the combined speeches file
    combined_speeches_file = os.path.join("CombinedStateOfUnionAddresses.txt")
    broken_links = []  # Track broken links
    with open(combined_speeches_file, 'w', encoding='utf-8') as combined_file:

        # Navigate Xpath to the tag with union addresses
        speech_links = html_etree.xpath('//*//div/dl/dt/span/a')

        # Iterate over each speech element and extract the information
        for speech in speech_links:
            # Extract president's name, date, and link to the speech
            full_speech_text = speech.text.strip()
            relative_link = speech.get('href')  # Get the relative URL for the speech
            full_link = urljoin(main_url, relative_link)  # Combine base URL with the relative link

            if '(' in full_speech_text and ')' in full_speech_text:
                # Split based on the last '(' to separate president and date
                president, date = full_speech_text.rsplit('(', 1)
                president = president.strip()
                date = date.strip(')')

                # Handle different date formats and convert to a standardized format
                try:
                    date = date.replace('th', '').replace('st', '').replace('nd', '').replace('rd', '').strip()  # Remove suffixes
                    date = datetime.strptime(date, "%B %d, %Y").date()  # Convert to date object
                except ValueError:
                    continue  # Skip if the date format is incorrect
            else:
                continue  

            # Print a processing message
            print(f"Processing speech for {president} ({date})")

            # Extract the speech content from the speech link
            speech_response = requests.get(full_link)
            speech_tree = html.fromstring(speech_response.content)

            # Find all <p> tags containing the speech text and join their content
            p_tags = speech_tree.xpath('//*/article/div/div/p')
            speech_text = '\n'.join([p.text_content().strip() for p in p_tags])

            # Check if the speech text is empty (broken link)
            if not speech_text.strip():
                print(f"No speech found for {president} ({date})")
                broken_links.append((president, date, full_link))

                # Insert NULL values for FILENAME_ADDRESS and TEXT_OF_ADDRESS
                insert_row_into_table(cursor, table, president, date, full_link, 'NULL', 'NULL')
                continue 

            # Saving speech text to a local file
            filename = write_to_file(output_directory, f"{president} ({date})", speech_text)

            # Insert the data into the SQL Server database
            insert_row_into_table(cursor, table, president, date, full_link, filename, speech_text)

            # Append the speech to the combined speeches file
            combined_file.write(f"{president} ({date})\n\n{speech_text}\n\n{'-'*80}\n\n")

    # Success messege for records stored in database 
    print(f"Records stored in the SQL database.")

    # Display broken links after processing
    display_broken_links(broken_links)
    

def connect_to_sql_server(server, database, table):
    """Connects to the SQL Server, drops the database if it exists, and creates a new database and table."""
    # Connect to SQL Server
    odbc_conn = pyodbc.connect('DRIVER={SQL Server};SERVER=' + server + ';Trusted_Connection=yes;') 
    odbc_conn.autocommit = True
    cursor = odbc_conn.cursor()

    # Set the database to single-user mode and drop it if it exists
    cursor.execute(f"""
    IF EXISTS (SELECT * FROM sys.databases WHERE name = '{database}')
    BEGIN
        ALTER DATABASE {database} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
        DROP DATABASE {database};
    END
    """)

    # Create the database and switch to it
    cursor.execute(f"CREATE DATABASE {database};")
    cursor.execute(f"USE {database};")

    # Drop the table if it exists, then create the table
    cursor.execute(f"""
    IF OBJECT_ID('{table}', 'U') IS NOT NULL
    DROP TABLE dbo.{table};
    
    CREATE TABLE dbo.{table} (
        NAME_OF_PRESIDENT VARCHAR(100),
        DATE_OF_UNION_ADDRESS DATE,
        LINK_TO_ADDRESS VARCHAR(255), 
        FILENAME_ADDRESS VARCHAR(255),
        TEXT_OF_ADDRESS NVARCHAR(MAX)
    );""")

    return cursor

def insert_row_into_table(cursor, table, name, date, link, file, text):
    """Inserts a single union address into the SQL Server database."""
    
    # Escape apostrophes to prevent SQL errors
    text = text.replace("'", "''")
    
    # Insert the speech data into the table
    cursor.execute(f"""
        INSERT INTO {table} (NAME_OF_PRESIDENT, DATE_OF_UNION_ADDRESS, LINK_TO_ADDRESS, FILENAME_ADDRESS, TEXT_OF_ADDRESS)
        VALUES ('{name}', '{date}', '{link}', '{file}', '{text}');
        """)

def write_to_file(output_directory, file_name, text):
    """Writes the speech to a local file on disk and returns the file path.""" 
    # Clean up the file name and construct the full file path
    clean_file_name = file_name.replace(',', '').replace(' ', '_')
    full_file_path = os.path.join(output_directory, f"{clean_file_name}.txt")
    # Write the speech text to the file
    with open(full_file_path, "w", encoding='utf-8') as text_file:
        text_file.write(text)
    return full_file_path

def display_broken_links(broken_links):
    """Displays any broken links encountered while scraping."""
    if broken_links:
        for president, date, _ in broken_links:
            print(f"broken link - {president} ({date})")
    else:
        print("No broken links encountered.")

# Run the main function
if __name__ == '__main__':
    main()
