import time
import sys
sys.path.append(r"c:\Users\nicks\Documents\401k_crm")

from api.database import SessionLocal
from api.sync import sync_dol_data
from api.models import Prospect

def main():
    db = SessionLocal()
    try:
        # Resolve tenant ID
        # Since we might have multiple tenants, let's get the first user's tenant or use a default one
        from api.models import User
        user = db.query(User).filter_by(email="advisor@example.com").first()
        if user:
            tenant_id = user.tenant_id
        else:
            tenant_id = "default_tenant"
            
        print(f"Running sync locally for tenant: {tenant_id}...")
        start = time.time()
        sync_dol_data(db, target_tenant_id=tenant_id)
        duration = time.time() - start
        
        count = db.query(Prospect).filter_by(tenant_id=tenant_id).count()
        print(f"Sync completed in {duration:.4f} seconds!")
        print(f"Total prospects in pipeline for {tenant_id}: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
