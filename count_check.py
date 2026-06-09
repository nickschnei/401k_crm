import sqlite3
c = sqlite3.connect("/app/prospects.db")
cur = c.cursor()
cur.execute("SELECT COUNT(*) FROM pipeline_prospects")
print("pipeline_prospects count:", cur.fetchone()[0])
cur.execute("SELECT tenant_id, COUNT(*) FROM pipeline_prospects GROUP BY tenant_id")
for row in cur.fetchall():
    print("  tenant:", row[0], "count:", row[1])
c.close()
