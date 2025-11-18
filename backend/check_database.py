import sqlite3
import os

db_path = 'catalogue.db'
if os.path.exists(db_path):
    print(f"Database exists: {db_path}")
    print(f"Database size: {os.path.getsize(db_path)} bytes")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # Check if catalogue table exists and has data
    try:
        cursor.execute("SELECT COUNT(*) FROM catalogue")
        count = cursor.fetchone()[0]
        print(f"Total records in catalogue: {count}")
        
        if count > 0:
            cursor.execute("SELECT title, author FROM catalogue LIMIT 5")
            sample = cursor.fetchall()
            print("Sample records:")
            for title, author in sample:
                print(f"  - {title} by {author}")
        
    except Exception as e:
        print(f"Error accessing catalogue table: {e}")
    
    conn.close()
else:
    print(f"Database NOT found: {db_path}")
    
    # Check if CSV exists
    csv_path = 'catalogue.csv'
    if os.path.exists(csv_path):
        print(f"CSV exists: {csv_path}")
        print(f"CSV size: {os.path.getsize(csv_path)} bytes")
    else:
        print(f"CSV NOT found: {csv_path}")