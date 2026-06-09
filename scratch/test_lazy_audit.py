import sys
import os
sys.path.append(os.getcwd())

from utils.audit_engine import run_plan_audit
from api.database import SessionLocal
from api.models import Form5500Audit, Prospect

print("Running test lazy-audit for EIN 188021660...")
try:
    # run audit on-demand
    run_plan_audit("188021660", ".")
    print("Plan audit completed successfully!")
    
    # check db to see if it exists
    db = SessionLocal()
    try:
        audit = db.query(Form5500Audit).filter_by(ein="188021660").first()
        if audit:
            print("Successfully saved to form_5500_audits!")
            print(f"- Employer: {audit.employer_name}")
            print(f"- Plan: {audit.plan_name}")
            print(f"- Schedule: {audit.schedule_type}")
            print(f"- Assets: ${audit.total_assets:,.2f}")
            print(f"- Participants: {audit.active_participants}")
            print(f"- Admin Expenses: ${audit.admin_expenses:,.2f}")
            print(f"- Corrective Distributions: ${audit.corrective_distributions:,.2f}")
        else:
            print("Error: Could not find audit record in DB!")
            
        prospect = db.query(Prospect).filter_by(ein="188021660").first()
        if prospect:
            print("Successfully updated pipeline_prospects!")
            print(f"- Employer: {prospect.employer_name}")
            print(f"- Assets: ${prospect.total_assets:,.2f}")
    finally:
        db.close()
except Exception as e:
    print("Failed running lazy-audit:", e)
