import sqlite3
import os

def setup_database():
    db_path = "knowledge.db"
    
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a sample table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        content TEXT NOT NULL
    )
    ''')
    
    # Insert some sample data
    sample_data = [
        ('Company Policy', 'Employees are entitled to 20 days of paid leave per year.'),
        ('Holiday Calendar', 'The office will be closed on December 25th for Christmas.'),
        ('Technical Support', 'The IT department is available from 9 AM to 5 PM, Monday to Friday.'),
        ('Office Location', 'The main office is located at 123 Tech Avenue, Silicon Valley.'),
        ('Project Alpha', 'Project Alpha is scheduled to be completed by June 2026.')
    ]
    
    cursor.executemany('INSERT INTO facts (topic, content) VALUES (?, ?)', sample_data)
    
    conn.commit()
    conn.close()
    print(f"Database '{db_path}' initialized with sample data.")

if __name__ == "__main__":
    setup_database()
