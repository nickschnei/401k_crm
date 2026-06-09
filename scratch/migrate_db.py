import sys
import os
sys.path.append(os.getcwd())

from api.database import engine, Base
from api.models import Prospect
from sqlalchemy import text

# Drop pipeline_prospects table
with engine.connect() as conn:
    print("Dropping pipeline_prospects table...")
    conn.execute(text("DROP TABLE IF EXISTS pipeline_prospects"))
    conn.commit()

# Recreate tables (this will create pipeline_prospects with the new schema)
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Database schema migration completed successfully!")
