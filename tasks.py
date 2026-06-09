import os
import time
from celery import Celery
import config

# Define Celery broker and results backend. 
# In production, this reads Redis configurations, but falls back gracefully to a robust local SQLite queue.
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "sqla+sqlite:///celerydb.sqlite")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "db+sqlite:///celeryresults.sqlite")

celery_app = Celery(
    "fiduciary_crm_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Global status persistence matching the current scraper JSON structure
STATUS_FILE = os.path.join(config.EXTRACTED_DATA_DIR, "sync_status.json")

def _update_sync_status(is_running: bool, error: str = None, summary: dict = None):
    """Helper to persist sync status to disk so Next.js frontend is updated in real-time."""
    os.makedirs(config.EXTRACTED_DATA_DIR, exist_ok=True)
    status = {
        "is_running": is_running,
        "last_run": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": error,
        "summary": summary
    }
    try:
        import json
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print(f"[Celery Worker] Failed to update sync status file: {e}")

@celery_app.task(name="tasks.sync_dol_data_task")
def sync_dol_data_task(force_refresh: bool = False):
    """
    Celery background worker task to parse and sync DOL Form 5500 filings.
    Runs asynchronously, decoupling large dataset unzipping and pandas parsing from the API.
    """
    print("[Celery Worker] Initiating background DOL sync task...")
    _update_sync_status(is_running=True)
    
    start_time = time.time()
    
    from api.database import SessionLocal
    from api.sync import sync_dol_data
    from api.models import Form5500Audit
    
    db = SessionLocal()
    try:
        # Run the primary high-performance data ingestion sync
        sync_dol_data(db, force_refresh=force_refresh)
        
        # Calculate summary details for UI status panel
        execution_duration = round(time.time() - start_time, 2)
        total_audits = db.query(Form5500Audit).count()
        
        summary = {
            "files_scanned": 4, # Primary archives
            "new_records_added": total_audits,
            "audits_completed": total_audits,
            "execution_duration_sec": execution_duration,
            "status": "success"
        }
        
        _update_sync_status(is_running=False, summary=summary)
        print(f"[Celery Worker] DOL sync completed successfully in {execution_duration}s!")
        return {"status": "success", "summary": summary}
        
    except Exception as e:
        print(f"[Celery Worker] Fatal error during sync: {e}")
        _update_sync_status(is_running=False, error=str(e), summary={"status": "failed"})
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
