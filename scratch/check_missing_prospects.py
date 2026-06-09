import sqlite3

conn = sqlite3.connect("prospects.db")
c = conn.cursor()

# Get all pipeline_prospects
c.execute("SELECT ein, employer_name, total_assets, active_participants FROM pipeline_prospects")
prospects = c.fetchall()

print(f"Total pipeline prospects: {len(prospects)}")
missing = 0
found_but_empty = 0

for ein, name, assets, participants in prospects:
    c.execute("SELECT total_assets, admin_expenses, corrective_distributions FROM form_5500_audits WHERE ein = ?", (ein,))
    audit = c.fetchone()
    if not audit:
        # Check Form5500Audit other table (form_5500_audit)
        c.execute("SELECT total_assets, admin_expenses, corrective_distributions FROM form_5500_audit WHERE ein = ?", (ein,))
        audit_old = c.fetchone()
        if audit_old:
            print(f"EIN {ein} ({name}) missing from form_5500_audits but found in form_5500_audit: {audit_old}")
        else:
            print(f"EIN {ein} ({name}) completely missing from both audit tables. Excel metrics: assets={assets}, participants={participants}")
            missing += 1
    else:
        # Check if assets is 0 or None
        if audit[0] is None or audit[0] == 0:
            print(f"EIN {ein} ({name}) found in form_5500_audits but has zero/empty metrics: {audit}")
            found_but_empty += 1

print(f"\nSummary: completely missing: {missing}, found but empty: {found_but_empty}")
conn.close()
