import sqlite3

def quick_view():
    conn = sqlite3.connect('job_listings.db')
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM job_listings")
    total = cursor.fetchone()[0]
    print(f"\nTotal Jobs Found: {total}")
    
    # Get latest 10 entries
    print("\nLatest 10 Job Listings:")
    cursor.execute("""
        SELECT job_title, company_name, location, salary
        FROM job_listings
        ORDER BY scraped_date DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print("\n-------------------")
        print(f"Title: {row[0]}")
        print(f"Company: {row[1]}")
        print(f"Location: {row[2]}")
        print(f"Salary: {row[3]}")
    
    conn.close()

if __name__ == "__main__":
    quick_view() 