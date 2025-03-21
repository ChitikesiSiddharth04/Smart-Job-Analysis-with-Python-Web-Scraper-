import sqlite3
from bs4 import BeautifulSoup
import requests
from Extractjobdeails import JobDetail, extract_email, extract_phone_number

class JobDetailsDataService:
    DB_PATH = "mydatabase.db"

    def add_job_details_from_link(self, link):
        list_of_jobs = self.fetch_job_details_from_link(link)
        
        conn = None
        cursor = None

        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()

            sql = """INSERT INTO job_detail 
                     (title_location, basic_details, qualifications, 
                      full_job_description, email, phone, apply_link) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)"""

            for job_detail in list_of_jobs:
                cursor.execute(sql, (
                    job_detail.title_location,
                    job_detail.basic_details,
                    job_detail.qualifications,
                    job_detail.full_job_description,
                    job_detail.email,
                    job_detail.phone,
                    job_detail.apply_link
                ))
                conn.commit()

                print(f"Inserted job: {job_detail.title_location}")

        except sqlite3.Error as e:
            print("Error while connecting to SQLite", e)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def fetch_job_details_from_link(self, link):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        }
        
        response = requests.get(link, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_details = []
            for job in soup.find_all('div', class_='SerpJob'):
                title_element = job.find('a', class_='chakra-button')
                basic_details = job.find('span', class_='chakra-text')
                description = job.find('div', class_='jobposting-snippet')
                apply_button = job.find('a', class_='chakra-button')

                job_detail = JobDetail(
                    title_location=title_element.text.strip() if title_element else "",
                    basic_details=basic_details.text.strip() if basic_details else "",
                    qualifications="",  # Extract if available
                    full_job_description=description.text.strip() if description else "",
                    email=extract_email(description.text) if description else "",
                    phone=extract_phone_number(description.text) if description else "",
                    apply_link=apply_button.get('href') if apply_button else ""
                )
                job_details.append(job_detail)
            
            return job_details
        else:
            print(f"Failed to retrieve content from {link}")
            return []

# Example usage:
# job_details_service = JobDetailsDataService()
# job_details_service.add_job_details_from_link("http://example.com/job-details")