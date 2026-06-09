import os
import sys

# Add the project path to PYTHONPATH
sys.path.append("/home/ubuntu/401k_crm")

from api.sync import sync_dol_data
from api.database import SessionLocal

db = SessionLocal()
try:
    print("Starting sync...")
    sync_dol_data(db, target_tenant_id="d50a0cb6-cb5e-4370-9438-bd0866041e4c")
    print("Sync complete!")
finally:
    db.close()
