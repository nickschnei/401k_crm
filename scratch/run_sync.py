import sys
sys.path.append('/app')

from api.sync import sync_dol_data
from api.database import SessionLocal

def main():
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else 'd50a0cb6-cb5e-4370-9438-bd0866041e4c'
    db = SessionLocal()
    try:
        print(f"Triggering sync for tenant: {tenant_id}")
        sync_dol_data(db, target_tenant_id=tenant_id)
        print("Sync completed successfully!")
    except Exception as e:
        print(f"Error during sync: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
