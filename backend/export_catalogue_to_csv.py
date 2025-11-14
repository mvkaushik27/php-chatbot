#!/usr/bin/env python3
"""
Export catalogue.db to catalogue.csv for FAISS indexing
This script reads from the SQLite database and exports to CSV format
"""

import sqlite3
import pandas as pd
import os

def export_catalogue_to_csv():
    """Export catalogue database to CSV file"""
    db_file = 'catalogue.db'
    csv_file = 'catalogue.csv'
    
    if not os.path.exists(db_file):
        print(f"Error: {db_file} not found")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_file)
        
        # Get table names
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Found tables: {[t[0] for t in tables]}")
        
        # Find the main catalogue table (usually 'biblio' or similar)
        # Try common table names
        for table_name in ['biblio', 'biblioitems', 'items', 'catalogue']:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1", conn)
                if not df.empty:
                    print(f"Using table: {table_name}")
                    # Read full table
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                    
                    # Export to CSV
                    df.to_csv(csv_file, index=False)
                    print(f"Successfully exported {len(df)} rows to {csv_file}")
                    conn.close()
                    return True
            except Exception as e:
                continue
        
        # If no standard table found, try the first table
        if tables:
            table_name = tables[0][0]
            print(f"Using first table: {table_name}")
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            df.to_csv(csv_file, index=False)
            print(f"Successfully exported {len(df)} rows to {csv_file}")
            conn.close()
            return True
        else:
            print("No tables found in database")
            conn.close()
            return False
            
    except Exception as e:
        print(f"Error exporting catalogue: {e}")
        return False

if __name__ == '__main__':
    success = export_catalogue_to_csv()
    exit(0 if success else 1)
