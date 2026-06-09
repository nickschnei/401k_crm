import sqlite3
import sys
import time
sys.path.append(".")

from utils.audit_engine import run_plan_audit

db_path = "prospects.db"
ein = "020444227"  # Ball Systems INC

# 1. Print current state in DB
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT employer_name, total_assets, admin_expenses, corrective_distributions FROM form_5500_audits WHERE ein = ?", (ein,))
before = c.fetchone()
print(f"Before audit: {before}")

# 2. Run plan audit with timing
start_time = time.time()
print("Running plan audit...")
run_plan_audit(ein, ".", db_path=db_path)
end_time = time.time()
print(f"Audit completed in {end_time - start_time:.4f} seconds!")

# 3. Print state in DB after audit
c.execute("SELECT employer_name, total_assets, admin_expenses, corrective_distributions, fee_ratio, compliance_failed FROM form_5500_audits WHERE ein = ?", (ein,))
after = c.fetchone()
print(f"After audit: {after}")
conn.close()
