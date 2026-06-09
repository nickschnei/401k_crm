import sqlite3

def check_users():
    conn = sqlite3.connect('prospects.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables in prospects.db: {tables}")
    
    for table in ['tenants', 'users']:
        if table in tables:
            print(f"\n--- Columns in {table} ---")
            cursor.execute(f"PRAGMA table_info({table});")
            for col in cursor.fetchall():
                print(f"  {col[1]} ({col[2]})")
            
            print(f"\n--- Records in {table} ---")
            cursor.execute(f"SELECT * FROM {table};")
            records = cursor.fetchall()
            print(f"  Total records: {len(records)}")
            for r in records[:10]:
                print(f"  {r}")
        else:
            print(f"\nTable '{table}' does NOT exist!")
            
    conn.close()

if __name__ == "__main__":
    check_users()
