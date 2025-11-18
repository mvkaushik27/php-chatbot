import sqlite3

conn = sqlite3.connect('catalogue.db')
cursor = conn.cursor()

print("=== Searching for Five Laws variations ===")

# Search for books with "five" in title
cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) LIKE '%five%'")
five_books = cursor.fetchall()
print(f"Books with 'five' in title: {len(five_books)}")
for title, author in five_books:
    print(f"  - {title} by {author}")

print("\n=== Searching for books with 'laws' in title ===")
cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) LIKE '%laws%'")
laws_books = cursor.fetchall()
print(f"Books with 'laws' in title: {len(laws_books)}")
for title, author in laws_books[:10]:  # Show first 10
    print(f"  - {title} by {author}")

print("\n=== Searching for Ranganathan books ===")
cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(author) LIKE '%ranganathan%'")
ranganathan_books = cursor.fetchall()
print(f"Books by Ranganathan: {len(ranganathan_books)}")
for title, author in ranganathan_books:
    print(f"  - {title} by {author}")

print("\n=== Searching for library science books ===")
cursor.execute("SELECT title, author FROM catalogue WHERE LOWER(title) LIKE '%library%science%'")
lib_sci_books = cursor.fetchall()
print(f"Books with 'library science' in title: {len(lib_sci_books)}")
for title, author in lib_sci_books[:5]:
    print(f"  - {title} by {author}")

conn.close()