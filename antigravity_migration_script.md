# 401(k) Fiduciary CRM Modernization Plan

This script is designed for an AI agent (Antigravity) to migrate the 401(k) CRM from a Streamlit prototype to a production-ready SaaS stack.

## Target Stack
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query.
- **Backend**: FastAPI, SQLAlchemy (Async), PostgreSQL, Alembic.
- **Auth**: Clerk (Backend Middleware + Frontend SDK).
- **Billing**: Stripe.
- **Data**: Redis + Celery/Arq for background DOL parsing.

## Phase 1: Backend Infrastructure (FastAPI + SQLA)
1. **Initialize SQLAlchemy Models**:
    - Create `models.py` in the `api/` directory.
    - Define `Prospect`, `PlanData`, `Audit`, and `Contact` models.
    - Use `PostgreSQL` as the primary database.
2. **Refactor `core.py` Logic**:
    - Decouple data parsing from API requests.
    - Create a `sync_dol_data` service that extracts ZIPs and populates the DB.
    - Update `api/prospects.py` to query the database using SQLAlchemy sessions instead of Pandas dataframes.
3. **Authentication**:
    - Finalize Clerk middleware in `utils/auth.py`.
    - Secure all `/api/v1/` routes.

## Phase 2: Frontend Foundation (Next.js)
1. **Initialize Next.js App**:
    - Run `npx create-next-app@latest frontend --typescript --tailwind --eslint`.
    - Initialize shadcn/ui: `npx shadcn-ui@latest init`.
2. **Setup API Client**:
    - Create a `services/api.ts` using Axios.
    - Set up `TanStack Query` providers.
3. **Theming & Layout**:
    - Create a Sidebar navigation matching the CRM flow (Pipeline, Discovery, Audits, Billing).

## Phase 3: Component Migration (Streamlit -> React)
1. **Metric Cards**: Convert `components/metrics.py` to React components using `lucide-react`.
2. **Pipeline View**: Rebuild `views/pipeline.py` using a TanStack Table with filtering and sorting.
3. **Audit Dashboard**: Convert the DOL audit view into a rich dashboard with charts (using Recharts or Tremor).
4. **Pitch Generator**: Rebuild the outreach pitch UI with a copy-to-clipboard feature and text editor.

## Phase 4: Data Ingestion & Background Tasks
1. **Setup Redis & Arq**:
    - Define worker tasks for ZIP extraction and CSV parsing.
    - Add a "Sync Data" button in the admin UI to trigger these tasks.
2. **Optimization**:
    - Add indexes to `EIN` and `Employer Name` columns in PostgreSQL.

---

### Instructions for Antigravity Agent:
1. **Research**: Start by reading `main.py`, `app.py`, and `api/prospects.py` to understand the current data flow.
2. **Step-by-Step Implementation**: Do NOT attempt to migrate everything at once.
    - Start by creating the `frontend` directory and setting up the basic layout.
    - Then, implement the `GET /prospects` API call in Next.js.
    - Gradually replace Streamlit views with Next.js pages.
3. **Preserve Logic**: Ensure the `dol_audit_engine.py` logic (which is the core IP) is preserved but called through a cleaner API interface.
