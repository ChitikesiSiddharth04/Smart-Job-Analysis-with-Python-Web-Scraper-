import sqlite3
from dataclasses import dataclass

@dataclass
class JobDetail:
    title_location: str
    basic_details: str
    qualifications: str
    full_job_description: str
    email: str
    phone: str
    apply_link: str

def initialize_database():
    try:
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_location TEXT,
                basic_details TEXT,
                qualifications TEXT,
                full_job_description TEXT,
                email TEXT,
                phone TEXT,
                apply_link TEXT
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def insert_job_detail(conn, job_detail):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO job_details (
                title_location, basic_details, qualifications, 
                full_job_description, email, phone, apply_link
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_detail.title_location,
            job_detail.basic_details,
            job_detail.qualifications,
            job_detail.full_job_description,
            job_detail.email,
            job_detail.phone,
            job_detail.apply_link
        ))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting job detail: {e}")

def main():
    # Test database structure with new apply_link field
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE example (
            id INTEGER PRIMARY KEY,
            content TEXT,
            apply_link TEXT
        )
    ''')

    # Test data
    test_content = "Job Description with apply link"
    test_apply_link = "https://www.simplyhired.com/apply/123"

    cursor.execute('INSERT INTO example (content, apply_link) VALUES (?, ?)', 
                  (test_content, test_apply_link))
    conn.commit()

    cursor.execute('SELECT * FROM example')
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Content: {row[1]}")
        print(f"Apply Link: {row[2]}")

    conn.close()

if __name__ == "__main__":
    main()