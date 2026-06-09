-- 401(k) CRM SaaS - Production PostgreSQL Database Schema
-- Provides multi-tenant data isolation, Clerk authentication profiles, and high-performance DOL filing indexes.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TENANTS TABLE (Multi-tenant subscription billing)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(50) DEFAULT 'free', -- 'free', 'pro', 'enterprise'
    subscription_status VARCHAR(50) DEFAULT 'inactive', -- 'active', 'trialing', 'canceled', 'past_due'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. USERS TABLE (Integrated with Clerk Authentication OIDC)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL, -- Clerk authenticated user profile link
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'advisor', -- 'advisor', 'admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. PIPELINE PROSPECTS TABLE (Tenant-isolated CRM outreach logs)
CREATE TABLE pipeline_prospects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    ein VARCHAR(9) NOT NULL,
    employer_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Lead', -- 'Lead', 'Researching', 'Cold Called', 'Meeting Set', 'Disqualified'
    notes TEXT DEFAULT '',
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    total_assets NUMERIC(20, 2),
    active_participants INTEGER,
    provider VARCHAR(255),
    industry VARCHAR(255),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tenant_prospect_ein UNIQUE (tenant_id, ein)
);

-- 4. FORM 5500 AUDITS CACHE TABLE (Highly optimized for > 700,000 filings)
CREATE TABLE form_5500_audits (
    ein VARCHAR(9) PRIMARY KEY,
    employer_name VARCHAR(255) NOT NULL,
    plan_name VARCHAR(255),
    schedule_type VARCHAR(10), -- 'H', 'I', 'SF'
    total_assets NUMERIC(20, 2) DEFAULT 0.00,
    active_participants INTEGER DEFAULT 0,
    total_eligible_employees INTEGER DEFAULT 0,
    admin_expenses NUMERIC(20, 2) DEFAULT 0.00,
    corrective_distributions NUMERIC(20, 2) DEFAULT 0.00,
    participation_rate NUMERIC(6, 4) DEFAULT 0.0000,
    fee_ratio NUMERIC(8, 6) DEFAULT 0.000000,
    compliance_failed BOOLEAN DEFAULT FALSE,
    fee_red_flag BOOLEAN DEFAULT FALSE,
    participation_red_flag BOOLEAN DEFAULT FALSE,
    dol_address VARCHAR(255),
    dol_city VARCHAR(150),
    dol_state VARCHAR(50),
    dol_zip VARCHAR(20),
    administrator_name VARCHAR(255),
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- --- TENANT DATA ISOLATION: ROW LEVEL SECURITY (RLS) ---
ALTER TABLE pipeline_prospects ENABLE ROW LEVEL SECURITY;

-- Dynamic isolation: A user can only see/edit prospects matching their user profile tenant_id
CREATE POLICY tenant_prospect_isolation ON pipeline_prospects
    FOR ALL
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM users 
            WHERE clerk_user_id = current_setting('app.current_clerk_id', true)
        )
    );

-- --- HIGH PERFORMANCE SEARCH INDEXES ---
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Composite index for rapid advisor geofencing and asset-scale filtering on filings
CREATE INDEX idx_form_5500_assets_participants ON form_5500_audits(total_assets, active_participants);

-- Trigram GIN indexes for extremely fast case-insensitive wildcard searches (LIKE/ILIKE)
CREATE INDEX idx_form_5500_employer_trgm ON form_5500_audits USING gin (employer_name gin_trgm_ops);
CREATE INDEX idx_form_5500_administrator_trgm ON form_5500_audits USING gin (administrator_name gin_trgm_ops);

-- Location-based B-tree indexes for state, city, and zip code geofencing
CREATE INDEX idx_form_5500_state_city ON form_5500_audits(dol_state, dol_city);
CREATE INDEX idx_form_5500_zip ON form_5500_audits(dol_zip);

-- Pipeline multi-tenant index tracking
CREATE INDEX idx_pipeline_tenant_ein ON pipeline_prospects(tenant_id, ein);
CREATE INDEX idx_pipeline_employer_name ON pipeline_prospects(employer_name);
