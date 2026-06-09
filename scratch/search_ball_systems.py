import sys
import os
sys.path.append(os.getcwd())

from api.database import SessionLocal
from api.models import Form5500Audit

db = SessionLocal()
try:
    print("Audits matching 'Ball Systems':")
    matches = db.query(Form5500Audit).filter(Form5500Audit.employer_name.ilike("%Ball Systems%")).all()
    for m in matches:
        print(f"- {m.employer_name} EIN={m.ein} Assets={m.total_assets} Participants={m.active_participants}")
finally:
    db.close()
