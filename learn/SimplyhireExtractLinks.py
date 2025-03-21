import cloudscraper
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SimplyHiredScraper:
    def __init__(self):
        # Expand user agents list
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0",
            "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1"
        ]
        
        # Add request delays
        self.min_delay = 10  # Minimum seconds between requests
        self.max_delay = 20  # Maximum seconds between requests
        
        # Session management
        self.session_requests = 0
        self.max_requests_per_session = 50  # Reset session after this many requests
        
        # Initialize scraper with additional options
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=950  # Add delay for JavaScript challenges
        )

    def get_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "TE": "Trailers",
            # Randomize viewport
            "Viewport-Width": str(random.randint(1024, 1920)),
            "Device-Memory": str(random.randint(4, 8))
        }

    def create_database(self):
        conn = sqlite3.connect('job_listings.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT,
                company_name TEXT,
                location TEXT,
                salary TEXT,
                job_description TEXT,
                job_link TEXT UNIQUE,
                posted_date TEXT,
                scraped_date DATETIME,
                requirements TEXT,
                job_type TEXT
            )
        ''')
        
        conn.commit()
        return conn, cursor

    def extract_job_details(self, job_card):
        try:
            # Extract job title
            title_elem = job_card.find('h2', class_='chakra-heading') or \
                        job_card.find('h3', class_='jobposting-title')
            job_title = title_elem.text.strip() if title_elem else "N/A"

            # Extract company name
            company_elem = job_card.find('span', {'data-testid': 'companyName'}) or \
                         job_card.find('span', class_='jobposting-company')
            company_name = company_elem.text.strip() if company_elem else "N/A"

            # Extract location
            location_elem = job_card.find('span', {'data-testid': 'searchSerpJobLocation'}) or \
                          job_card.find('span', class_='jobposting-location')
            location = location_elem.text.strip() if location_elem else "N/A"

            # Extract salary if available
            salary_elem = job_card.find('div', {'data-testid': 'searchSerpJobSalary'}) or \
                         job_card.find('span', class_='jobposting-salary')
            salary = salary_elem.text.strip() if salary_elem else "Not specified"

            # Extract job description
            desc_elem = job_card.find('div', {'data-testid': 'searchSerpJobDescription'}) or \
                       job_card.find('p', class_='jobposting-snippet')
            description = desc_elem.text.strip() if desc_elem else "N/A"

            # Extract job link
            link_elem = job_card.find('a', {'data-testid': 'searchSerpJobTitle'}) or \
                       job_card.find('a', href=True)
            job_link = link_elem['href'] if link_elem else ""
            if job_link and not job_link.startswith('http'):
                job_link = f"https://www.simplyhired.com{job_link}"

            # Extract job type
            job_type_elem = job_card.find('span', class_='jobposting-type')
            job_type = job_type_elem.text.strip() if job_type_elem else "Not specified"

            return {
                'job_title': job_title,
                'company_name': company_name,
                'location': location,
                'salary': salary,
                'job_description': description,
                'job_link': job_link,
                'job_type': job_type,
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'requirements': self.extract_requirements(description)
            }
        except Exception as e:
            logging.error(f"Error extracting job details: {str(e)}")
            return None

    def extract_requirements(self, description):
        # Look for common requirement indicators in the description
        requirement_indicators = [
            "requirements:", "qualifications:", "what you'll need:",
            "skills:", "experience:", "must have:"
        ]
        
        description_lower = description.lower()
        for indicator in requirement_indicators:
            if indicator in description_lower:
                start_idx = description_lower.find(indicator)
                # Get the text after the indicator until the next period or end of string
                end_idx = description.find('.', start_idx)
                if end_idx == -1:
                    end_idx = len(description)
                return description[start_idx:end_idx].strip()
        return "Requirements not specified"

    def make_request(self, url):
        try:
            # Implement exponential backoff
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    # Rotate session if needed
                    if self.session_requests >= self.max_requests_per_session:
                        self.scraper = cloudscraper.create_scraper(
                            browser={
                                'browser': 'chrome',
                                'platform': 'windows',
                                'desktop': True
                            }
                        )
                        self.session_requests = 0
                    
                    # Add random delay
                    delay = random.uniform(self.min_delay, self.max_delay)
                    time.sleep(delay)
                    
                    # Make request
                    response = self.scraper.get(
                        url,
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    self.session_requests += 1
                    
                    if response.status_code == 200:
                        return response
                    elif response.status_code == 403:
                        logging.warning("Access forbidden. Waiting longer...")
                        time.sleep(60)  # Wait a minute before retry
                    elif response.status_code == 429:
                        logging.warning("Rate limited. Cooling down...")
                        time.sleep(120)  # Wait two minutes before retry
                    
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            
            return None
        
        except Exception as e:
            logging.error(f"Request failed: {str(e)}")
            return None

    def scrape_jobs(self, search_url, max_pages=3):
        conn, cursor = self.create_database()
        total_jobs = 0

        try:
            for page in range(1, max_pages + 1):
                url = f"{search_url}&pn={page}" if page > 1 else search_url
                print(f"\nTrying to scrape: {url}")
                
                response = self.make_request(url)
                if not response:
                    print(f"Failed to fetch page {page}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Updated selectors for current SimplyHired structure
                job_cards = soup.find_all('div', class_='css-0')  # This is the current main container class
                
                print(f"Found {len(job_cards)} potential job cards on page {page}")
                
                if not job_cards:
                    print("Trying alternative selectors...")
                    job_cards = (
                        soup.find_all('div', {'data-testid': 'searchSerpJobCard'}) or
                        soup.find_all('article', class_='chakra-card') or
                        soup.find_all('div', class_='SerpJob-jobCard')
                    )
                    print(f"Found {len(job_cards)} job cards with alternative selectors")

                if not job_cards:
                    print("\nDebug Information:")
                    print("First 500 characters of response:")
                    print(response.text[:500])
                    print("\nChecking for common elements:")
                    print(f"Found any job titles: {bool(soup.find_all('h2', class_='chakra-heading'))}")
                    print(f"Found any links: {len(soup.find_all('a'))}")
                    continue

                for job_card in job_cards:
                    job_details = self.extract_job_details(job_card)
                    if job_details:
                        print(f"\nFound Job: {job_details['job_title']} at {job_details['company_name']}")
                        try:
                            cursor.execute('''
                                INSERT OR IGNORE INTO job_listings 
                                (job_title, company_name, location, salary, job_description, 
                                 job_link, posted_date, scraped_date, requirements, job_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                job_details['job_title'],
                                job_details['company_name'],
                                job_details['location'],
                                job_details['salary'],
                                job_details['job_description'],
                                job_details['job_link'],
                                job_details['posted_date'],
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                job_details['requirements'],
                                job_details['job_type']
                            ))
                            conn.commit()
                            total_jobs += 1
                        except sqlite3.Error as e:
                            logging.error(f"Database error: {str(e)}")
                    else:
                        print("Failed to extract job details from card")

        finally:
            conn.close()
            logging.info(f"Scraping completed. Total jobs found: {total_jobs}")
            return total_jobs

def main():
    scraper = SimplyHiredScraper()
    default_url = "https://www.simplyhired.com/search?q=python+developer&l=remote"
    search_url = input("Enter the SimplyHired search URL (or press Enter for default): ").strip() or default_url
    max_pages = int(input("Enter maximum number of pages to scrape (default 3): ") or 3)
    
    print("\nStarting scraper...")
    print(f"Target URL: {search_url}")
    print(f"Max Pages: {max_pages}")
    
    total_jobs = scraper.scrape_jobs(search_url, max_pages)
    print(f"\nScraping completed!")
    print(f"Total jobs scraped: {total_jobs}")
    
    if total_jobs == 0:
        print("\nNo jobs were scraped. Possible issues:")
        print("1. Website might be blocking automated access")
        print("2. Search returned no results")
        print("3. HTML structure might have changed")
        print("\nCheck the generated log files for more details")

if __name__ == "__main__":
    main()
