import sqlite3
from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests

@dataclass
class JobDetail:
    title_location: str
    basic_details: str
    qualifications: str
    full_job_description: str

    def __init__(self, html_content=None, url=None):
        if url:
            html_content = self.fetch_job_details(url)
        elif html_content is None:
            raise ValueError("Either html_content or url must be provided.")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Assuming the HTML structure has specific tags or classes for each detail
        self.title_location = soup.find('div', class_='title-location').get_text(strip=True)
        self.basic_details = soup.find('div', class_='basic-details').get_text(strip=True)
        self.qualifications = soup.find('div', class_='qualifications').get_text(strip=True)
        self.full_job_description = soup.find('div', class_='full-job-description').get_text(strip=True)

    def fetch_job_details(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def get_title_location(self):
        return self.title_location

    def set_title_location(self, title_location):
        self.title_location = title_location

    def get_basic_details(self):
        return self.basic_details

    def set_basic_details(self, basic_details):
        self.basic_details = basic_details

    def get_qualifications(self):
        return self.qualifications

    def set_qualifications(self, qualifications):
        self.qualifications = qualifications

    def get_full_job_description(self):
        return self.full_job_description

    def set_full_job_description(self, full_job_description):
        self.full_job_description = full_job_description

    def save_to_db(self, db_name='job_details.db'):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_location TEXT,
                basic_details TEXT,
                qualifications TEXT,
                full_job_description TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO job_details (title_location, basic_details, qualifications, full_job_description)
            VALUES (?, ?, ?, ?)
        ''', (self.title_location, self.basic_details, self.qualifications, self.full_job_description))
        conn.commit()
        conn.close()

    @staticmethod
    def load_from_db(db_name='job_details.db'):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM job_details')
        rows = cursor.fetchall()
        conn.close()
        return [JobDetail.from_row(row) for row in rows]

    @staticmethod
    def from_row(row):
        _, title_location, basic_details, qualifications, full_job_description = row
        return JobDetail(f'''
            <div class="title-location">{title_location}</div>
            <div class="basic-details">{basic_details}</div>
            <div class="qualifications">{qualifications}</div>
            <div class="full-job-description">{full_job_description}</div>
        ''')

# Example of creating a JobDetail instance with a URL
url = "https://example.com/job-details"  # Replace with the actual job details URL
job_detail = JobDetail(url=url)  # Now you can create an instance using a URL

# Save to database
job_detail.save_to_db()

# Load from database
loaded_jobs = JobDetail.load_from_db()
for job in loaded_jobs:
    print("Title and Location:", job.get_title_location())
    print("Basic Details:", job.get_basic_details())
    print("Qualifications:", job.get_qualifications())
    print("Full Job Description:", job.get_full_job_description())