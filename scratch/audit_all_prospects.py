import sqlite3
import sys
sys.path.append(".")

from utils.audit_engine import run_plan_audit

db_path = "prospects.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all pipeline_prospects
c.execute("SELECT ein, employer_name, total_assets, active_participants FROM pipeline_prospects")
prospects = c.fetchall()

print(f"Total pipeline prospects to verify: {len(prospects)}")
audited_count = 0

for ein, name, assets, participants in prospects:
    c.execute("SELECT total_assets FROM form_5500_audits WHERE ein = ?", (ein,))
    row = c.fetchone()
    
    if not row or row[0] is None or row[0] == 0.0:
        print(f"Auditing '{name}' (EIN: {ein})...")
        run_plan_audit(ein, ".", db_path=db_path)
        audited_count += 1

print(f"\nCompleted! Audited and enriched {audited_count} prospects.")
conn.close()
