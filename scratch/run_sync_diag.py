import subprocess
import os

key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"

def run_remote_commands():
    # Shell script to run on remote host to execute diagnostic python code inside container
    remote_script = """
    cd /home/ubuntu/401k_crm
    echo "=== Running Sync Diag inside container ==="
    sudo docker compose exec -T web-backend python -c "
import sys
import pandas as pd
from api.database import SessionLocal
from api.models import Prospect, Tenant, Form5500Audit
from api.sync import normalize_ein

excel_file = '/app/Combined 401k Prospecting Plan.xlsx'
db = SessionLocal()
try:
    tenant_id = 'd50a0cb6-cb5e-4370-9438-bd0866041e4c'
    tenant = db.query(Tenant).filter_by(id=tenant_id).first()
    print('Tenant:', tenant.id if tenant else 'None')
    
    prospects_df = pd.read_excel(excel_file, header=5)
    print('Original columns:', list(prospects_df.columns))
    
    prospects_df = prospects_df.rename(columns={
        'Company': 'Employer Name',
        'Contact': 'Contact Name',
        'EMAIL': 'EMAIL'
    })
    print('Renamed columns:', list(prospects_df.columns))
    
    print('Length of df:', len(prospects_df))
    
    processed = 0
    errors = 0
    skipped = 0
    
    for idx, row in prospects_df.iterrows():
        employer_name = str(row.get('Employer Name')).strip()
        if not employer_name or employer_name.lower() in ['nan', 'none', 'company']:
            skipped += 1
            continue
            
        ein = None
        if 'EIN' in row.index and pd.notna(row.get('EIN')):
            ein = normalize_ein(row.get('EIN'))
            
        # Try to find EIN by looking up
        if not ein:
            try:
                # 1. Try exact match
                audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name == employer_name).first()
                if not audit_match:
                    audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name == employer_name.upper()).first()
                if not audit_match:
                    audit_match = db.query(Form5500Audit).filter(Form5500Audit.employer_name.like(f'{employer_name}%')).first()
                
                if audit_match:
                    ein = audit_match.ein
                else:
                    import hashlib
                    hash_obj = hashlib.md5(employer_name.encode('utf-8'))
                    ein = ''.join(c for c in hash_obj.hexdigest() if c.isdigit())[:9].zfill(9)
            except Exception as e:
                print(f'Error looking up EIN for {employer_name}: {e}')
                errors += 1
                continue
                
        print(f'Row {idx}: {employer_name} -> EIN {ein}')
        processed += 1
        if processed >= 5:
            print('... (truncated for brevity)')
            break
            
    print(f'Summary - Processed: {processed}, Skipped: {skipped}, Errors: {errors}')

except Exception as e:
    print('Outer ERROR:', e)
finally:
    db.close()
"
    """
    
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{ip}",
        "bash"
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=remote_script.encode('utf-8'))
    
    import sys
    print("STDOUT:")
    sys.stdout.buffer.write(stdout)
    print("\nSTDERR:")
    sys.stdout.buffer.write(stderr)

if __name__ == "__main__":
    run_remote_commands()
