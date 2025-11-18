import sqlite3
import csv
import os

def create_and_populate_database():
    """Re-create the catalogue database from CSV"""
    
    csv_file = 'catalogue.csv'
    db_file = 'catalogue.db'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    print(f"Reading from: {csv_file}")
    print(f"Creating database: {db_file}")
    
    # Remove existing database
    if os.path.exists(db_file):
        os.remove(db_file)
        print("Removed existing database")
    
    # Create new database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create catalogue table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalogue (
            id INTEGER PRIMARY KEY,
            call_number TEXT,
            isbn TEXT,
            title TEXT,
            subtitle TEXT,
            author TEXT,
            pages TEXT,
            publisher TEXT,
            year INTEGER,
            accession_number TEXT
        )
    ''')
    
    # Read and import CSV data
    imported_count = 0
    failed_count = 0
    
    with open(csv_file, 'r', encoding='utf-8', errors='replace') as file:
        csv_reader = csv.reader(file)
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                if len(row) >= 9:  # Ensure we have enough columns
                    cursor.execute('''
                        INSERT INTO catalogue 
                        (call_number, isbn, title, subtitle, author, pages, publisher, year, accession_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', [
                        row[1] if len(row) > 1 else '',  # call_number
                        row[2] if len(row) > 2 else '',  # isbn
                        row[3] if len(row) > 3 else '',  # title
                        row[4] if len(row) > 4 else '',  # subtitle
                        row[5] if len(row) > 5 else '',  # author
                        row[6] if len(row) > 6 else '',  # pages
                        row[7] if len(row) > 7 else '',  # publisher
                        int(row[8]) if len(row) > 8 and row[8].strip().isdigit() else None,  # year
                        row[9] if len(row) > 9 else ''   # accession_number
                    ])
                    imported_count += 1
                    
                    # Show progress every 1000 rows
                    if imported_count % 1000 == 0:
                        print(f"Imported {imported_count} records...")
                        
                else:
                    failed_count += 1
                    if failed_count <= 5:  # Show first few failures
                        print(f"Row {row_num}: Insufficient columns ({len(row)}): {row}")
                        
            except Exception as e:
                failed_count += 1
                if failed_count <= 5:
                    print(f"Row {row_num}: Error - {e}: {row}")
    
    conn.commit()
    print(f"\nImport complete!")
    print(f"Successfully imported: {imported_count} records")
    print(f"Failed to import: {failed_count} records")
    
    # Test search for Five Laws book
    print(f"\n=== Testing Five Laws search ===")
    cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) LIKE '%five%laws%'")
    results = cursor.fetchall()
    print(f"Found {len(results)} books with 'five laws' in title:")
    for title, author in results:
        print(f"  - {title} by {author}")
    
    conn.close()

if __name__ == "__main__":
    create_and_populate_database()