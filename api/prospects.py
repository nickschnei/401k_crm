import uuid
from sqlalchemy import text
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from api.database import get_async_db
from api.models import Prospect, Form5500Audit, User, Tenant
from utils.auth import ClerkUser, get_current_user

router = APIRouter()

async def resolve_tenant_id(db: AsyncSession, current_user: ClerkUser) -> str:
    """Helper to dynamically resolve or auto-provision Tenant/User and return tenant_id."""
    # Check if user exists
    user_stmt = select(User).where(User.clerk_user_id == current_user.clerk_id)
    user_res = await db.execute(user_stmt)
    db_user = user_res.scalar_one_or_none()
    
    if not db_user:
        # Auto-provision user & tenant
        tenant_stmt = select(Tenant).where(Tenant.id == "default_tenant")
        tenant_res = await db.execute(tenant_stmt)
        db_tenant = tenant_res.scalar_one_or_none()
        if not db_tenant:
            db_tenant = Tenant(
                id="default_tenant",
                company_name="Default Advisory Firm",
                subscription_tier="free",
                subscription_status="active"
            )
            db.add(db_tenant)
            await db.flush()
        
        db_user = User(
            id=str(uuid.uuid4()),
            clerk_user_id=current_user.clerk_id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            tenant_id="default_tenant",
            role="advisor"
        )
        db.add(db_user)
        await db.flush()
        await db.commit()
        
    return db_user.tenant_id or "default_tenant"

class UpdateStatusRequest(BaseModel):
    status: str
    notes: str

class ProspectResponse(BaseModel):
    employer_name: Optional[str] = None
    ein: Optional[str] = None
    total_assets: Optional[float] = None
    participants: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    industry: Optional[str] = None
    provider: Optional[str] = None
    administrator: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

@router.get("/", response_model=List[ProspectResponse])
async def get_prospects(
    search: Optional[str] = Query(None),
    min_assets: Optional[float] = Query(0),
    max_assets: Optional[float] = Query(None),
    min_participants: Optional[int] = Query(0),
    max_participants: Optional[int] = Query(None),
    status: Optional[str] = Query("All"),
    industry: Optional[str] = Query("All"),
    provider: Optional[str] = Query("All"),
    administrator: Optional[str] = Query("All"),
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve filtered prospects from the database using SQLAlchemy sessions."""
    try:
        # Resolve user tenant and apply RLS contexts
        tenant_id = await resolve_tenant_id(db, current_user)
        
        # Set session clerk ID for Postgres native RLS policies
        if not db.bind.dialect.name == "sqlite":
            await db.execute(
                text("SELECT set_config('app.current_clerk_id', :clerk_id, true)"),
                {"clerk_id": current_user.clerk_id}
            )
            
        # Construct dynamic query with primary software-level multi-tenant isolation
        stmt = select(Prospect, Form5500Audit).outerjoin(Form5500Audit, Prospect.ein == Form5500Audit.ein).where(Prospect.tenant_id == tenant_id)
        
        # Apply filters
        if status != "All":
            stmt = stmt.where(Prospect.status == status)
            
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Prospect.employer_name.ilike(search_pattern),
                    Prospect.ein.ilike(search_pattern),
                    Prospect.notes.ilike(search_pattern),
                    Prospect.contact_name.ilike(search_pattern),
                    Prospect.contact_email.ilike(search_pattern),
                    Form5500Audit.plan_name.ilike(search_pattern),
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

        # Execute query
        result = await db.execute(stmt)
        rows = result.all()
        
        # If DB is empty, lazy-sync it first!
        if not rows and not search and min_assets == 0 and status == "All":
            print(f"[API] Database empty for tenant {tenant_id}. Running initial sync...")
            import asyncio
            def _run_sync(tid: str):
                from api.sync import sync_dol_data
                from api.database import SessionLocal
                sync_db = SessionLocal()
                try:
                    sync_dol_data(sync_db, target_tenant_id=tid)
                finally:
                    sync_db.close()
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _run_sync, tenant_id)
            
            # Close and reopen async session to get fresh connection
            await db.close()
            from api.database import AsyncSessionLocal
            async with AsyncSessionLocal() as fresh_db:
                result = await fresh_db.execute(stmt)
                rows = result.all()

        results = []
        seen_eins = set()
        for prospect, audit in rows:
            if prospect.ein in seen_eins:
                continue
            seen_eins.add(prospect.ein)
            total_assets = 0.0
            if prospect.total_assets is not None:
                total_assets = float(prospect.total_assets)
            elif audit and audit.total_assets is not None:
                total_assets = float(audit.total_assets)

            participants = 0
            if prospect.active_participants is not None:
                participants = prospect.active_participants
            elif audit and audit.active_participants is not None:
                participants = audit.active_participants

            provider = "Fidelity"
            if prospect.provider:
                provider = prospect.provider
            elif audit:
                provider = "Vanguard" if audit.total_assets and audit.total_assets > 10000000 else "Fidelity"

            industry = prospect.industry or "Professional Services"

            results.append({
                "employer_name": prospect.employer_name,
                "ein": prospect.ein,
                "total_assets": total_assets,
                "participants": participants,
                "status": prospect.status or "Lead",
                "notes": prospect.notes or "",
                "industry": industry,
                "provider": provider,
                "administrator": audit.administrator_name if audit else None,
                "contact_name": prospect.contact_name,
                "contact_email": prospect.contact_email,
                "contact_phone": prospect.contact_phone,
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ein}", response_model=ProspectResponse)
async def get_prospect_by_ein(
    ein: str, 
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieve detailed information for a single prospect EIN."""
    try:
        # Resolve user tenant and apply RLS contexts
        tenant_id = await resolve_tenant_id(db, current_user)
        
        # Set session clerk ID for Postgres native RLS policies
        if not db.bind.dialect.name == "sqlite":
            await db.execute(
                text("SELECT set_config('app.current_clerk_id', :clerk_id, true)"),
                {"clerk_id": current_user.clerk_id}
            )
            
        clean_ein = "".join(c for c in str(ein) if c.isdigit())[-9:].zfill(9)
        stmt = select(Prospect, Form5500Audit).outerjoin(Form5500Audit, Prospect.ein == Form5500Audit.ein).where(Prospect.ein == clean_ein).where(Prospect.tenant_id == tenant_id)
        result = await db.execute(stmt)
        row = result.first()
        
        if not row:
            # Try discovery mode lookup directly
            audit_stmt = select(Form5500Audit).where(Form5500Audit.ein == clean_ein)
            audit_result = await db.execute(audit_stmt)
            audit = audit_result.scalar_one_or_none()
            if not audit:
                raise HTTPException(status_code=404, detail=f"Prospect with EIN {ein} not found.")
            
            return {
                "employer_name": audit.employer_name,
                "ein": audit.ein,
                "total_assets": float(audit.total_assets),
                "participants": audit.active_participants,
                "status": "Lead",
                "notes": "",
                "industry": "Professional Services",
                "provider": "Fidelity",
                "administrator": audit.administrator_name,
                "contact_name": None,
                "contact_email": None,
                "contact_phone": None,
            }
            
        prospect, audit = row
        total_assets = 0.0
        if prospect.total_assets is not None:
            total_assets = float(prospect.total_assets)
        elif audit and audit.total_assets is not None:
            total_assets = float(audit.total_assets)

        participants = 0
        if prospect.active_participants is not None:
            participants = prospect.active_participants
        elif audit and audit.active_participants is not None:
            participants = audit.active_participants

        provider = "Fidelity"
        if prospect.provider:
            provider = prospect.provider
        elif audit:
            provider = "Vanguard" if audit.total_assets and audit.total_assets > 10000000 else "Fidelity"

        industry = prospect.industry or "Professional Services"

        return {
            "employer_name": prospect.employer_name,
            "ein": prospect.ein,
            "total_assets": total_assets,
            "participants": participants,
            "status": prospect.status or "Lead",
            "notes": prospect.notes or "",
            "industry": industry,
            "provider": provider,
            "administrator": audit.administrator_name if audit else None,
            "contact_name": prospect.contact_name,
            "contact_email": prospect.contact_email,
            "contact_phone": prospect.contact_phone,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{ein}/status")
async def update_prospect_status(
    ein: str, 
    body: UpdateStatusRequest, 
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update CRM pipeline status and notes for a specific corporate prospect."""
    try:
        # Resolve user tenant and apply RLS contexts
        tenant_id = await resolve_tenant_id(db, current_user)
        
        # Set session clerk ID for Postgres native RLS policies
        if not db.bind.dialect.name == "sqlite":
            await db.execute(
                text("SELECT set_config('app.current_clerk_id', :clerk_id, true)"),
                {"clerk_id": current_user.clerk_id}
            )
            
        clean_ein = "".join(c for c in str(ein) if c.isdigit())[-9:].zfill(9)
        stmt = select(Prospect).where(Prospect.ein == clean_ein).where(Prospect.tenant_id == tenant_id)
        result = await db.execute(stmt)
        prospect = result.scalar_one_or_none()
        
        if not prospect:
            audit_stmt = select(Form5500Audit).where(Form5500Audit.ein == clean_ein)
            audit_result = await db.execute(audit_stmt)
            audit = audit_result.scalar_one_or_none()
            
            employer_name = audit.employer_name if audit else "Unknown Prospect"
            prospect = Prospect(
                tenant_id=tenant_id,
                ein=clean_ein,
                employer_name=employer_name,
                status=body.status,
                notes=body.notes
            )
            db.add(prospect)
        else:
            prospect.status = body.status
            prospect.notes = body.notes
            
        await db.commit()
        return {
            "success": True,
            "message": f"Pipeline record for EIN {ein} updated to {body.status} successfully."
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{ein}/enrich", response_model=ProspectResponse)
async def enrich_prospect(
    ein: str, 
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Query Apollo/Hunter contact database to find HR Director contact info for a prospect."""
    try:
        # Resolve user tenant and apply RLS contexts
        tenant_id = await resolve_tenant_id(db, current_user)
        
        # Set session clerk ID for Postgres native RLS policies
        if not db.bind.dialect.name == "sqlite":
            await db.execute(
                text("SELECT set_config('app.current_clerk_id', :clerk_id, true)"),
                {"clerk_id": current_user.clerk_id}
            )
            
        clean_ein = "".join(c for c in str(ein) if c.isdigit())[-9:].zfill(9)
        stmt = select(Prospect).where(Prospect.ein == clean_ein).where(Prospect.tenant_id == tenant_id)
        result = await db.execute(stmt)
        prospect = result.scalar_one_or_none()
        
        employer_name = "prospect"
        if prospect:
            employer_name = prospect.employer_name
        else:
            audit_stmt = select(Form5500Audit).where(Form5500Audit.ein == clean_ein)
            audit_result = await db.execute(audit_stmt)
            audit = audit_result.scalar_one_or_none()
            if audit:
                employer_name = audit.employer_name
        
        from services.enrichment import enrich_prospect_contact
        enriched = enrich_prospect_contact(clean_ein, employer_name)
        
        if not prospect:
            prospect = Prospect(
                tenant_id=tenant_id,
                ein=clean_ein,
                employer_name=employer_name,
                status="Lead",
                notes=""
            )
            db.add(prospect)
            
        prospect.contact_name = enriched.get("contact_name")
        prospect.contact_email = enriched.get("contact_email")
        prospect.contact_phone = enriched.get("contact_phone")
        
        await db.commit()
        
        updated_stmt = select(Prospect, Form5500Audit).outerjoin(Form5500Audit, Prospect.ein == Form5500Audit.ein).where(Prospect.ein == clean_ein)
        updated_result = await db.execute(updated_stmt)
        prospect, audit = updated_result.first()
        
        total_assets = 0.0
        if prospect.total_assets is not None:
            total_assets = float(prospect.total_assets)
        elif audit and audit.total_assets is not None:
            total_assets = float(audit.total_assets)

        participants = 0
        if prospect.active_participants is not None:
            participants = prospect.active_participants
        elif audit and audit.active_participants is not None:
            participants = audit.active_participants

        provider = "Fidelity"
        if prospect.provider:
            provider = prospect.provider
        elif audit:
            provider = "Vanguard" if audit.total_assets and audit.total_assets > 10000000 else "Fidelity"

        industry = prospect.industry or "Professional Services"

        return {
            "employer_name": prospect.employer_name,
            "ein": prospect.ein,
            "total_assets": total_assets,
            "participants": participants,
            "status": prospect.status or "Lead",
            "notes": prospect.notes or "",
            "industry": industry,
            "provider": provider,
            "administrator": audit.administrator_name if audit else None,
            "contact_name": prospect.contact_name,
            "contact_email": prospect.contact_email,
            "contact_phone": prospect.contact_phone,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
