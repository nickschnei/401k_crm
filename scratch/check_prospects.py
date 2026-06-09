import sqlite3

def check_prospects():
    conn = sqlite3.connect('prospects.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, tenant_id FROM users;")
    users = cursor.fetchall()
    print("--- Active Users ---")
    for u in users:
        print(f"User ID: {u[0]} | Email: {u[1]} | Tenant ID: {u[2]}")
        
    cursor.execute("SELECT tenant_id, COUNT(*) FROM pipeline_prospects GROUP BY tenant_id;")
    prospects_count = cursor.fetchall()
    print("\n--- Prospects Count per Tenant ---")
    for p in prospects_count:
        print(f"Tenant ID: {p[0]} | Prospects count: {p[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_prospects()
