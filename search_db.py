import sqlite3

def find_links():
    conn = sqlite3.connect('C:/Users/nicks/Documents/401k_crm/prospects.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    for table in tables:
        table_name = table[0]
        print(f"\nSearching table: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columns: {columns}")
        
        # Search for 'http' or 'link' or 'url' in any column
        for col in columns:
            try:
                cursor.execute(f"SELECT {col} FROM {table_name} WHERE {col} LIKE '%http%' OR {col} LIKE '%www%';")
                results = cursor.fetchall()
                if results:
                    print(f"Found matches in {col}: {results[:5]}")
            except:
                pass
    
    conn.close()

if __name__ == "__main__":
    find_links()
