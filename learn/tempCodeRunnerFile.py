import requests
from bs4 import BeautifulSoup
import re
import sqlite3

class JobDetail:
    def __init__(self, title_location, basic_details, qualification, full_job_description, email, phone):
        self.title_location = title_location
        self.basic_details = basic_details
        self.qualification = qualification
        self.full_job_description = full_job_description
        self.email = email
        self.phone = phone

    def __str__(self):
        return f"JobDetail(titleLocation='{self.title_location}', basicDetails='{self.basic_details}', " \
               f"qualification='{self.qualification}', fullJobDescription='{self.full_job_description}', " \
               f"email='{self.email}', phone='{self.phone}')"

def extract_email(text):
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(email_regex, text)
    return match.group(0) if match else ""

def extract_phone_number(text):
    phone_regex = r"\+?[0-9]{1,3}[-.\s]?\(?[0-9]{2,4}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}"
    match = re.search(phone_regex, text)
    return match.group(0) if match else ""

def extract_data_from_page(soup):
    list_of_jobs = []
    items = soup.select("#job-list li")

    for item in items:
        child_elements = item.select(".css-1ebprri")

        title_location = child_elements[0].text if len(child_elements) > 0 else ""
        basic_details = child_elements[1].text if len(child_elements) > 1 else ""
        qualification = child_elements[2].text if len(child_elements) > 2 else ""
        full_job_description = child_elements[3].text if len(child_elements) > 3 else ""

        email = extract_email(full_job_description)
        phone = extract_phone_number(full_job_description)

        job_detail = JobDetail(title_location, basic_details, qualification, full_job_description, email, phone)
        list_of_jobs.append(job_detail)

    return list_of_jobs

def create_database():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS JobDetail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_location TEXT,
            basic_details TEXT,
            qualification TEXT,
            full_job_description TEXT,
            email TEXT,
            phone TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_job_detail(conn, job_detail):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO JobDetail (title_location, basic_details, qualification, full_job_description, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (job_detail.title_location, job_detail.basic_details, job_detail.qualification, job_detail.full_job_description, job_detail.email, job_detail.phone))
    conn.commit()

def main():
    url = "https://www.simplyhired.co.in/search?q=java&l=hyderabad%2C+telangana"
    conn = create_database()

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        list_of_jobs = extract_data_from_page(soup)
        for job in list_of_jobs:
            print(job)
            insert_job_detail(conn, job)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
