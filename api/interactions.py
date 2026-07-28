import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.database import get_async_db
from api.models import Interaction, Prospect, User, Tenant
from api.prospects import resolve_tenant_id
from utils.auth import ClerkUser, get_current_user

router = APIRouter()

class InteractionCreate(BaseModel):
    prospect_id: Optional[str] = None
    contact_name: str
    interaction_type: str  # 'Call', 'Email', 'Meeting', 'Other'
    notes: str
    interaction_date: Optional[datetime] = None

class InteractionUpdate(BaseModel):
    contact_name: Optional[str] = None
    interaction_type: Optional[str] = None
    notes: Optional[str] = None
    interaction_date: Optional[datetime] = None

class InteractionResponse(BaseModel):
    id: str
    tenant_id: str
    prospect_id: Optional[str] = None
    employer_name: Optional[str] = None
    ein: Optional[str] = None
    contact_name: str
    interaction_date: datetime
    interaction_type: str
    notes: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[InteractionResponse])
async def get_interactions(
    prospect_id: Optional[str] = Query(None),
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve all logged interactions for the current tenant, with optional prospect filtering."""
    try:
        tenant_id = await resolve_tenant_id(db, current_user)
        
        stmt = (
            select(Interaction, Prospect)
            .outerjoin(Prospect, Interaction.prospect_id == Prospect.id)
            .where(Interaction.tenant_id == tenant_id)
        )
        
        if prospect_id:
            stmt = stmt.where(Interaction.prospect_id == prospect_id)
            
        # Order by interaction_date descending
        stmt = stmt.order_by(desc(Interaction.interaction_date))
        
        res = await db.execute(stmt)
        rows = res.all()
        
        results = []
        for interaction, prospect in rows:
            results.append(
                InteractionResponse(
                    id=interaction.id,
                    tenant_id=interaction.tenant_id,
                    prospect_id=interaction.prospect_id,
                    employer_name=prospect.employer_name if prospect else "Unknown Employer",
                    ein=prospect.ein if prospect else None,
                    contact_name=interaction.contact_name,
                    interaction_date=interaction.interaction_date,
                    interaction_type=interaction.interaction_type,
                    notes=interaction.notes,
                    created_at=interaction.created_at,
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=InteractionResponse)
async def create_interaction(
    body: InteractionCreate,
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Log a new interaction linked to a prospect."""
    try:
        tenant_id = await resolve_tenant_id(db, current_user)
        
        # Verify prospect belongs to tenant if prospect_id is provided
        employer_name = None
        ein = None
        if body.prospect_id:
            p_stmt = select(Prospect).where(Prospect.id == body.prospect_id).where(Prospect.tenant_id == tenant_id)
            p_res = await db.execute(p_stmt)
            prospect = p_res.scalar_one_or_none()
            if not prospect:
                raise HTTPException(status_code=404, detail="Prospect not found for this tenant.")
            employer_name = prospect.employer_name
            ein = prospect.ein
            
        new_interaction = Interaction(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            prospect_id=body.prospect_id,
            contact_name=body.contact_name,
            interaction_date=body.interaction_date or datetime.now(),
            interaction_type=body.interaction_type,
            notes=body.notes,
        )
        
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)
        
        return InteractionResponse(
            id=new_interaction.id,
            tenant_id=new_interaction.tenant_id,
            prospect_id=new_interaction.prospect_id,
            employer_name=employer_name,
            ein=ein,
            contact_name=new_interaction.contact_name,
            interaction_date=new_interaction.interaction_date,
            interaction_type=new_interaction.interaction_type,
            notes=new_interaction.notes,
            created_at=new_interaction.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{id}", response_model=InteractionResponse)
async def update_interaction(
    id: str,
    body: InteractionUpdate,
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update details of an existing interaction log."""
    try:
        tenant_id = await resolve_tenant_id(db, current_user)
        
        stmt = (
            select(Interaction, Prospect)
            .outerjoin(Prospect, Interaction.prospect_id == Prospect.id)
            .where(Interaction.id == id)
            .where(Interaction.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise HTTPException(status_code=404, detail="Interaction log not found.")
            
        interaction, prospect = row
        
        if body.contact_name is not None:
            interaction.contact_name = body.contact_name
        if body.interaction_type is not None:
            interaction.interaction_type = body.interaction_type
        if body.notes is not None:
            interaction.notes = body.notes
        if body.interaction_date is not None:
            interaction.interaction_date = body.interaction_date
            
        await db.commit()
        await db.refresh(interaction)
        
        return InteractionResponse(
            id=interaction.id,
            tenant_id=interaction.tenant_id,
            prospect_id=interaction.prospect_id,
            employer_name=prospect.employer_name if prospect else None,
            ein=prospect.ein if prospect else None,
            contact_name=interaction.contact_name,
            interaction_date=interaction.interaction_date,
            interaction_type=interaction.interaction_type,
            notes=interaction.notes,
            created_at=interaction.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}")
async def delete_interaction(
    id: str,
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete an interaction log."""
    try:
        tenant_id = await resolve_tenant_id(db, current_user)
        
        stmt = select(Interaction).where(Interaction.id == id).where(Interaction.tenant_id == tenant_id)
        res = await db.execute(stmt)
        interaction = res.scalar_one_or_none()
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction log not found.")
            
        await db.delete(interaction)
        await db.commit()
        
        return {"success": True, "message": "Interaction log deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
