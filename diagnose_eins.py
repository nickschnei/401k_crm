import sys
sys.path.append("/app")

import pandas as pd
from api.sync import normalize_ein
from api.models import Form5500Audit
from api.database import SessionLocal

db = SessionLocal()

excel_file = "Combined 401k Prospecting Plan.xlsx"
prospects_df = pd.read_excel(excel_file, header=0)

if 'Employer Name' not in prospects_df.columns:
    if 'Company' in prospects_df.columns:
        prospects_df = prospects_df.rename(columns={'Company': 'Employer Name'})
    else:
        prospects_df['Employer Name'] = "Unknown"

prospects_df = prospects_df.dropna(subset=['Employer Name'])

seen = {}
duplicates = 0
for idx, row in prospects_df.iterrows():
    employer_name = str(row.get('Employer Name')).strip()
    if not employer_name or employer_name.lower() in ["nan", "none", "company"]:
        continue
    
    ein = None
    if 'EIN' in row.index and pd.notna(row.get('EIN')):
        ein = normalize_ein(row.get('EIN'))
    
    if not ein:
        audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name.ilike(f"%{employer_name}%")).first()
        if audit_match:
            ein = audit_match.ein
            print(f"  FUZZY MATCH: '{employer_name}' -> EIN={ein} (matched: '{audit_match.employer_name}')")
        else:
            import hashlib
            hash_obj = hashlib.md5(employer_name.encode('utf-8'))
            ein = "".join(c for c in hash_obj.hexdigest() if c.isdigit())[:9].zfill(9)
            print(f"  HASH FALLBACK: '{employer_name}' -> EIN={ein}")
    else:
        print(f"  EXCEL EIN: '{employer_name}' -> EIN={ein}")

    if ein in seen:
        duplicates += 1
        print(f"    ** DUPLICATE EIN {ein} (first was: '{seen[ein]}')")
    else:
        seen[ein] = employer_name

print(f"\nTotal rows: {len(prospects_df)}")
print(f"Unique EINs: {len(seen)}")
print(f"Duplicate EINs: {duplicates}")

db.close()
