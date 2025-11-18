import sqlite3

conn = sqlite3.connect('catalogue.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(catalogue)")
columns = cursor.fetchall()

print("Current database schema:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()