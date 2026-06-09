import uuid
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
    subscription_tier = Column(String(50), default="free")  # 'free', 'pro', 'enterprise'
    subscription_status = Column(String(50), default="inactive")  # 'active', 'trialing', 'canceled', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    prospects = relationship("Prospect", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    clerk_user_id = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), default="advisor")  # 'advisor', 'admin'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="users")


class Prospect(Base):
    __tablename__ = "pipeline_prospects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    ein = Column(String(9), nullable=False, index=True)
    employer_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="Lead")  # 'Lead', 'Researching', 'Cold Called', 'Meeting Set', 'Disqualified'
    notes = Column(Text, default="")
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    total_assets = Column(Numeric(20, 2), nullable=True)
    active_participants = Column(Integer, nullable=True)
    provider = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="prospects")

    __table_args__ = (
        UniqueConstraint("tenant_id", "ein", name="unique_tenant_prospect_ein"),
    )


class Form5500Audit(Base):
    __tablename__ = "form_5500_audits"

    ein = Column(String(9), primary_key=True)
    employer_name = Column(String(255), nullable=False, index=True)
    plan_name = Column(String(255), nullable=True)
    schedule_type = Column(String(10), nullable=True)  # 'H', 'I', 'SF'
    total_assets = Column(Numeric(20, 2), default=0.00)
    active_participants = Column(Integer, default=0)
    total_eligible_employees = Column(Integer, default=0)
    admin_expenses = Column(Numeric(20, 2), default=0.00)
    corrective_distributions = Column(Numeric(20, 2), default=0.00)
    participation_rate = Column(Numeric(6, 4), default=0.0000)
    fee_ratio = Column(Numeric(8, 6), default=0.000000)
    compliance_failed = Column(Boolean, default=False)
    fee_red_flag = Column(Boolean, default=False)
    participation_red_flag = Column(Boolean, default=False)
    dol_address = Column(String(255), nullable=True)
    dol_city = Column(String(150), nullable=True)
    dol_state = Column(String(50), nullable=True)
    dol_zip = Column(String(20), nullable=True)
    administrator_name = Column(String(255), nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
ProspectModel = Prospect
AuditModel = Form5500Audit
