import sqlite3
from bs4 import BeautifulSoup
import requests  # Add this import at the top with other imports

def insert_parsed_data():
    # Get URL input from user
    url = input("Please enter the URL to scrape: ")
    
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Fetch HTML data from the URL with headers
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_data = response.text
        
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return

    # SQLite database connection
    db_path = 'mydatabase.db'  # Path to your SQLite database file

    # Parse the HTML data using BeautifulSoup
    soup = BeautifulSoup(html_data, 'html.parser')
    try:
        name_elem = soup.find('p', string=lambda x: x and 'Name:' in x)
        age_elem = soup.find('p', string=lambda x: x and 'Age:' in x)
        city_elem = soup.find('p', string=lambda x: x and 'City:' in x)
        zipcode_elem = soup.find('p', string=lambda x: x and 'Zipcode:' in x)
        
        if not all([name_elem, age_elem, city_elem, zipcode_elem]):
            print("Error: Could not find all required elements in the HTML content")
            return
            
        name = name_elem.get_text().split(': ')[1]
        age = age_elem.get_text().split(': ')[1]
        city = city_elem.get_text().split(': ')[1]
        zipcode = zipcode_elem.get_text().split(': ')[1]
    except Exception as e:
        print(f"Error parsing HTML content: {e}")
        return

    # Create a JSON-like dictionary from the parsed data
    json_data = {
        "name": name,
        "age": age,
        "address": {
            "city": city,
            "zipcode": zipcode
        }
    }

    conn = None  # Initialize conn to None
    try:
        # Establish the database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simply_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                json_data TEXT
            )
        ''')
        conn.commit()

        # SQL INSERT query to insert JSON data
        sql = "INSERT INTO simply_table (json_data) VALUES (?)"

        # Execute the insert statement
        cursor.execute(sql, (str(json_data),))

        # Commit the transaction
        conn.commit()

        # Check if insert was successful
        if cursor.rowcount > 0:
            print("A new record was inserted successfully!")

    except sqlite3.Error as e:
        print(f"Error: {e}")

    finally:
        # Close the database connection
        if conn:
            cursor.close()
            conn.close()
            print("Database connection closed")

if __name__ == "__main__":
    insert_parsed_data()

