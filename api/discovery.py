from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from api.database import get_async_db
from api.models import Form5500Audit
from services.scraper import run_nightly_dol_sync, get_sync_status

router = APIRouter()

class DiscoveryResponse(BaseModel):
    employer_name: Optional[str] = None
    plan_name: Optional[str] = None
    total_assets: Optional[float] = None
    participants: Optional[int] = None
    dol_address: Optional[str] = None
    dol_city: Optional[str] = None
    dol_state: Optional[str] = None
    dol_zip: Optional[str] = None
    administrator: Optional[str] = None
    ein: Optional[str] = None

@router.get("/", response_model=List[DiscoveryResponse])
async def get_discovery_filings(
    search: Optional[str] = Query(None),
    min_assets: Optional[float] = Query(0),
    max_assets: Optional[float] = Query(None),
    min_participants: Optional[int] = Query(0),
    max_participants: Optional[int] = Query(None),
    industry: Optional[str] = Query("All"),
    provider: Optional[str] = Query("All"),
    administrator: Optional[str] = Query("All"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve raw DOL filings from discovery database with live filters."""
    try:
        stmt = select(Form5500Audit)
        
        # Apply filters
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Form5500Audit.employer_name.ilike(search_pattern),
                    Form5500Audit.plan_name.ilike(search_pattern),
                    Form5500Audit.ein.ilike(search_pattern),
                    Form5500Audit.dol_address.ilike(search_pattern),
                    Form5500Audit.dol_city.ilike(search_pattern),
                    Form5500Audit.dol_state.ilike(search_pattern),
                    Form5500Audit.dol_zip.ilike(search_pattern),
                    Form5500Audit.administrator_name.ilike(search_pattern),
                )
            )
            
        if min_assets and min_assets > 0:
            stmt = stmt.where(Form5500Audit.total_assets >= min_assets)
        if max_assets and max_assets > 0:
            stmt = stmt.where(Form5500Audit.total_assets <= max_assets)
            
        if min_participants and min_participants > 0:
            stmt = stmt.where(Form5500Audit.active_participants >= min_participants)
        if max_participants and max_participants > 0:
            stmt = stmt.where(Form5500Audit.active_participants <= max_participants)
            
        if administrator != "All":
            stmt = stmt.where(Form5500Audit.administrator_name == administrator)

        # Execute query
        result = await db.execute(stmt)
        filings = result.scalars().all()
        
        results = []
        for filing in filings:
            results.append({
                "employer_name": filing.employer_name,
                "plan_name": filing.plan_name or "401(k) Savings Plan",
                "total_assets": float(filing.total_assets) if filing.total_assets is not None else 0.0,
                "participants": filing.active_participants or 0,
                "dol_address": filing.dol_address,
                "dol_city": filing.dol_city,
                "dol_state": filing.dol_state,
                "dol_zip": filing.dol_zip,
                "administrator": filing.administrator_name,
                "ein": filing.ein,
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def trigger_dol_sync(background_tasks: BackgroundTasks):
    """Trigger incremental DOL Form 5500 background sync sweeps using Celery."""
    try:
        status = get_sync_status()
        if status.get("is_running"):
            return {
                "success": False,
                "message": "DOL background sync is already in progress."
            }
        
        try:
            # Attempt to delegate to Celery asynchronous background worker
            from tasks import sync_dol_data_task
            task = sync_dol_data_task.delay(force_refresh=True)
            return {
                "success": True,
                "message": "DOL background sync successfully initiated via Celery worker.",
                "task_id": task.id
            }
        except Exception as queue_err:
            # Fallback to FastAPI BackgroundTasks thread if broker is unreachable
            print(f"[API] Celery broker unreachable: {queue_err}. Falling back to background thread.")
            from tasks import sync_dol_data_task
            background_tasks.add_task(sync_dol_data_task, True)
            return {
                "success": True,
                "message": "DOL background sync successfully initiated (local fallback thread)."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def check_sync_status():
    """Retrieve the current background sync progress status."""
    try:
        return get_sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
