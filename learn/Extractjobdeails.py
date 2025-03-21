import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from datetime import datetime
import logging
import re
import random

def create_database():
    conn = sqlite3.connect('job_listings.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            description TEXT,
            job_link TEXT,
            posted_date TEXT,
            scraped_date DATETIME
        )
    ''')
    
    conn.commit()
    return conn, cursor

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

def save_to_database(job_listings, conn, cursor):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for job in job_listings:
        cursor.execute('''
            INSERT INTO jobs (title, company, location, salary, description, job_link, posted_date, scraped_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job['Title'],
            job['Company'],
            job['Location'],
            job['Salary'],
            job['Description'],
            job['Job Link'],
            job['Posted Date'],
            current_time
        ))
    
    conn.commit()

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15'
        ]
        self.current_agent = 0

    def get_random_headers(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }

    def scrape_page(self, url):
        job_listings = []
        try:
            # Add delay before request
            time.sleep(random.uniform(2, 5))
            
            # Use random headers
            headers = self.get_random_headers()
            response = self.session.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=30
            )
            
            
            if response.status_code == 403:
                print("Access denied. Waiting longer before retry...")
                time.sleep(10)  # Wait longer before retry
                return []
            
            # Handle potential cloudflare or other protection
            if response.status_code == 403:
                print("Access denied. Trying with alternative approach...")
                # You might want to implement additional bypass methods here
                return []
                
            response.raise_for_status()
            
            # Verify we got HTML content
            if 'text/html' not in response.headers.get('Content-Type', ''):
                print("Received non-HTML response")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we're blocked or got a captcha
            if 'captcha' in response.text.lower() or 'blocked' in response.text.lower():
                print("Detected captcha or blocking page")
                return []

            # Rest of your scraping logic...
            job_cards = soup.find_all('div', class_='SerpJob-jobCard')
            
            if not job_cards:
                print("No job cards found. Site structure might have changed.")
                return []

            # Process job cards...
            for card in job_cards:
                try:
                    job_data = self.extract_job_data(card)
                    if job_data:
                        job_listings.append(job_data)
                except Exception as e:
                    logging.error(f"Error extracting job data: {str(e)}")
                    continue

            return job_listings

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return []

    def extract_job_data(self, card):
        try:
            title = card.find('h3', class_='jobposting-title').text.strip()
            company = card.find('span', class_='jobposting-company').text.strip()
            location = card.find('span', class_='jobposting-location').text.strip()
            
            # Get job link
            link_element = card.find('a')
            job_link = link_element['href'] if link_element else ''
            if job_link and not job_link.startswith('http'):
                job_link = f"https://www.simplyhired.co.in{job_link}"
            
            # Try to get salary if available
            try:
                salary = card.find('span', class_='jobposting-salary').text.strip()
            except:
                salary = "Not specified"
            
            # Try to get description if available
            try:
                description = card.find('p', class_='jobposting-snippet').text.strip()
            except:
                description = "No description available"
            
            return {
                'Title': title,
                'Company': company,
                'Location': location,
                'Salary': salary,
                'Description': description,
                'Job Link': job_link,
                'Posted Date': datetime.now().strftime('%Y-%m-%d')
            }
        except Exception as e:
            logging.error(f"Error extracting job data: {str(e)}")
            return None

def scrape_all_pages(base_url, conn, cursor, max_pages=10):
    total_jobs = 0
    scraper = JobScraper()  # Create an instance of JobScraper
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}&pn={page}"
            
        print(f"Scraping page {page}...")
        
        jobs = scraper.scrape_page(url)  # Use scrape_page instead of scrape_job_details
        if not jobs:
            break
            
        save_to_database(jobs, conn, cursor)
        total_jobs += len(jobs)
        print(f"Saved {len(jobs)} jobs from page {page}")
        
        time.sleep(2)  # Be nice to the server
        
    return total_jobs

def display_sample_results(cursor, limit=5):
    cursor.execute('''
        SELECT title, company, location, salary, description, job_link, posted_date
        FROM jobs
        ORDER BY scraped_date DESC
        LIMIT ?
    ''', (limit,))
    
    results = cursor.fetchall()
    
    print("\nSample Job Listings:")
    for job in results:
        print("\n-------------------")
        print(f"Title: {job[0]}")
        print(f"Company: {job[1]}")
        print(f"Location: {job[2]}")
        print(f"Salary: {job[3]}")
        print(f"Description: {job[4][:200]}...")
        print(f"Job Link: {job[5]}")
        print(f"Posted Date: {job[6]}")

def main():
    # Create database connection
    conn, cursor = create_database()
    
    try:
        default_url = "https://www.simplyhired.co.in/search?q=java&l=hyderabad%2C+telangana"
        url = input("Enter the job search URL (press Enter to use default): ").strip() or default_url
        
        max_pages = int(input("Enter maximum number of pages to scrape (default 10): ") or 10)
        
        print("Scraping job details... Please wait...")
        total_jobs = scrape_all_pages(url, conn, cursor, max_pages)
        
        if total_jobs > 0:
            print(f"\nSuccessfully scraped and saved {total_jobs} job listings")
            display_sample_results(cursor)
        else:
            print("No job listings found")
            
    finally:
        # Close database connection
        conn.close()

class JobDetail:
    def __init__(self, title_location, basic_details, qualifications, 
                 full_job_description, email, phone, apply_link):
        self.title_location = title_location
        self.basic_details = basic_details
        self.qualifications = qualifications
        self.full_job_description = full_job_description
        self.email = email
        self.phone = phone
        self.apply_link = apply_link

def extract_email(text):
    # Add your email extraction logic here
    # For example, using regex to find email patterns
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

if __name__ == "__main__":
    main()
