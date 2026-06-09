import sqlite3

def wipe_users():
    conn = sqlite3.connect('prospects.db')
    cursor = conn.cursor()
    
    print("Pre-wipe status:")
    cursor.execute("SELECT id, email, clerk_user_id FROM users;")
    print("Users:", cursor.fetchall())
    cursor.execute("SELECT id, company_name FROM tenants;")
    print("Tenants:", cursor.fetchall())
    
    # Delete custom users (keeping the default mock user if it exists)
    cursor.execute("DELETE FROM users WHERE email != 'advisor@example.com';")
    print(f"Deleted custom users. Rows affected: {cursor.rowcount}")
    
    # Delete custom tenants (keeping the default tenant)
    cursor.execute("DELETE FROM tenants WHERE id != 'default_tenant';")
    print(f"Deleted custom tenants. Rows affected: {cursor.rowcount}")
    
    conn.commit()
    
    print("\nPost-wipe status:")
    cursor.execute("SELECT id, email, clerk_user_id FROM users;")
    print("Users:", cursor.fetchall())
    cursor.execute("SELECT id, company_name FROM tenants;")
    print("Tenants:", cursor.fetchall())
    
    conn.close()

if __name__ == "__main__":
    wipe_users()
