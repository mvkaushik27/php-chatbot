import sqlite3
import sys
import os

# Test the current search function
db_path = 'catalogue.db'
if not os.path.exists(db_path):
    print("Database not found!")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Testing Five Laws Book Search ===")

test_queries = [
    "The Five Laws of Library Science",
    "The Five Laws of Library Science book", 
    "Five Laws of Library Science",
    "five laws",
    "library science"
]

for query in test_queries:
    print(f"\nTesting: '{query}'")
    
    # Test exact match
    cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) = LOWER(?)", [query])
    exact = cursor.fetchall()
    print(f"  Exact matches: {len(exact)}")
    
    # Test fuzzy match (LIKE)
    cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) LIKE LOWER(?)", [f"%{query}%"])
    fuzzy = cursor.fetchall()
    print(f"  Fuzzy matches: {len(fuzzy)}")
    if fuzzy:
        for title, author in fuzzy[:3]:
            print(f"    - {title} by {author}")

# Test the exact title from CSV
print(f"\n=== Testing Exact CSV Title ===")
csv_title = "The Five Laws of Library Science/ "
cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) LIKE LOWER(?)", [f"%{csv_title.strip()}%"])
results = cursor.fetchall()
print(f"CSV title matches: {len(results)}")
for title, author in results:
    print(f"  - {title} by {author}")

conn.close()