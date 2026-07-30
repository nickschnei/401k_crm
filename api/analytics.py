from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, case, or_
from api.database import get_async_db
from api.models import Prospect, Form5500Audit, Interaction
from utils.auth import ClerkUser, get_current_user
from api.prospects import resolve_tenant_id

router = APIRouter()

class StageSummary(BaseModel):
    stage: str
    count: int
    total_assets: float
    percentage: float

class ProviderSummary(BaseModel):
    provider: str
    count: int
    total_assets: float
    red_flag_count: int

class ActivitySummary(BaseModel):
    interaction_type: str
    count: int

class FollowupHealth(BaseModel):
    overdue: int
    today: int
    upcoming: int
    completed: int

class AnalyticsSummaryResponse(BaseModel):
    total_prospects: int
    total_assets: float
    overall_conversion_rate: float
    funnel: List[StageSummary]
    activities: List[ActivitySummary]
    providers: List[ProviderSummary]
    followup_health: FollowupHealth

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    current_user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve aggregated pipeline conversion analytics, provider displacement matrices,
    and interaction activity counts for the active tenant.
    """
    tenant_id = await resolve_tenant_id(db, current_user)
    
    if not db.bind.dialect.name == "sqlite":
        await db.execute(
            text("SELECT set_config('app.current_clerk_id', :clerk_id, true)"),
            {"clerk_id": current_user.clerk_id}
        )

    # 1. Fetch all prospects for tenant
    stmt_prospects = select(Prospect).where(Prospect.tenant_id == tenant_id)
    res_prospects = await db.execute(stmt_prospects)
    prospects = res_prospects.scalars().all()

    total_prospects = len(prospects)
    total_assets = sum(float(p.total_assets or 0.0) for p in prospects)

    # Stages breakdown
    stages = ["Lead", "Researching", "Cold Called", "Meeting Set", "Disqualified"]
    stage_counts = {s: 0 for s in stages}
    stage_assets = {s: 0.0 for s in stages}

    for p in prospects:
        st = p.status or "Lead"
        if st in stage_counts:
            stage_counts[st] += 1
            stage_assets[st] += float(p.total_assets or 0.0)
        else:
            stage_counts["Lead"] += 1
            stage_assets["Lead"] += float(p.total_assets or 0.0)

    funnel_list = []
    for s in stages:
        cnt = stage_counts[s]
        pct = (cnt / total_prospects * 100.0) if total_prospects > 0 else 0.0
        funnel_list.append(StageSummary(
            stage=s,
            count=cnt,
            total_assets=stage_assets[s],
            percentage=round(pct, 1)
        ))

    meeting_set_cnt = stage_counts["Meeting Set"]
    overall_conversion = (meeting_set_cnt / total_prospects * 100.0) if total_prospects > 0 else 0.0

    # 2. Provider displacement analysis
    provider_map = {}
    for p in prospects:
        prov = p.provider or "Unspecified"
        if prov not in provider_map:
            provider_map[prov] = {"count": 0, "total_assets": 0.0, "red_flags": 0}
        provider_map[prov]["count"] += 1
        provider_map[prov]["total_assets"] += float(p.total_assets or 0.0)

    # Fetch audit flags for provider displacement
    eins = [p.ein for p in prospects if p.ein]
    if eins:
        audit_stmt = select(Form5500Audit).where(Form5500Audit.ein.in_(eins))
        res_audits = await db.execute(audit_stmt)
        audits = res_audits.scalars().all()
        audit_map = {a.ein: a for a in audits}

        for p in prospects:
            prov = p.provider or "Unspecified"
            a = audit_map.get(p.ein)
            if a and (a.fee_red_flag or a.participation_red_flag or a.compliance_failed):
                provider_map[prov]["red_flags"] += 1

    provider_list = [
        ProviderSummary(
            provider=prov,
            count=data["count"],
            total_assets=data["total_assets"],
            red_flag_count=data["red_flags"]
        )
        for prov, data in sorted(provider_map.items(), key=lambda item: item[1]["total_assets"], reverse=True)
    ]

    # 3. Activity breakdowns & follow-up task health
    interaction_stmt = select(Interaction).where(Interaction.tenant_id == tenant_id)
    res_interactions = await db.execute(interaction_stmt)
    interactions = res_interactions.scalars().all()

    type_counts = {"Call": 0, "Email": 0, "Meeting": 0, "Note": 0}
    overdue = 0
    today = 0
    upcoming = 0
    completed = 0

    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")

    for i in interactions:
        itype = i.interaction_type or "Note"
        if itype in type_counts:
            type_counts[itype] += 1
        else:
            type_counts["Note"] += 1

        if i.followup_completed:
            completed += 1
        elif i.followup_date:
            fdate_str = i.followup_date.strftime("%Y-%m-%d") if hasattr(i.followup_date, 'strftime') else str(i.followup_date)[:10]
            if fdate_str < today_str:
                overdue += 1
            elif fdate_str == today_str:
                today += 1
            else:
                upcoming += 1

    activity_list = [ActivitySummary(interaction_type=k, count=v) for k, v in type_counts.items()]

    return AnalyticsSummaryResponse(
        total_prospects=total_prospects,
        total_assets=total_assets,
        overall_conversion_rate=round(overall_conversion, 1),
        funnel=funnel_list,
        activities=activity_list,
        providers=provider_list[:6],
        followup_health=FollowupHealth(
            overdue=overdue,
            today=today,
            upcoming=upcoming,
            completed=completed
        )
    )
