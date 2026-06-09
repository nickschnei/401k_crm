import sys
import os
sys.path.append(os.getcwd())

from api.database import SessionLocal
from api.models import Prospect, Form5500Audit, Tenant

db = SessionLocal()
try:
    tenant_count = db.query(Tenant).count()
    prospect_count = db.query(Prospect).count()
    audit_count = db.query(Form5500Audit).count()
    print(f"Tenants: {tenant_count}")
    print(f"Prospects (pipeline_prospects): {prospect_count}")
    print(f"Audits (form_5500_audits): {audit_count}")
    
    if prospect_count > 0:
        print("First 3 prospects:")
        for p in db.query(Prospect).limit(3):
            print(f"- {p.employer_name} ({p.ein}) status={p.status} contact={p.contact_name}")
finally:
    db.close()
