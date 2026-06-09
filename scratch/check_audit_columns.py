import sqlite3

conn = sqlite3.connect("prospects.db")
c = conn.cursor()

print("--- form_5500_audit columns ---")
c.execute("PRAGMA table_info(form_5500_audit)")
for col in c.fetchall():
    print(col)

print("\n--- form_5500_audits columns ---")
c.execute("PRAGMA table_info(form_5500_audits)")
for col in c.fetchall():
    print(col)

conn.close()
