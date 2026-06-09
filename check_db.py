import sqlite3

conn = sqlite3.connect("prospects.db")
c = conn.cursor()

print("--- TABLES ---")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print(tables)

for table in tables:
    try:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"Table '{table}': {count} records")
    except Exception as e:
        print(f"Table '{table}': error: {e}")

print("--- USERS ---")
try:
    c.execute("SELECT id, email, first_name, last_name, tenant_id FROM users")
    for row in c.fetchall():
        print(row)
except Exception as e:
    print(e)

print("--- TENANTS ---")
try:
    c.execute("SELECT id, name FROM tenants")
    for row in c.fetchall():
        print(row)
except Exception as e:
    print(e)

print("--- PROSPECTS BY TENANT ---")
try:
    c.execute("SELECT tenant_id, COUNT(*) FROM prospects GROUP BY tenant_id")
    for row in c.fetchall():
        print(row)
except Exception as e:
    print(e)

conn.close()
