import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import config
from api import prospects, discovery, audits, billing, auth

app = FastAPI(
    title="401(k) Fiduciary CRM SaaS API",
    description="High-performance backend API to handle Form 5500 filings, contact enrichment, and pipeline updates.",
    version="1.0.0",
)

# Configure CORS for modern React/Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Database Auto-Migrations
@app.on_event("startup")
async def run_startup_migrations():
    """Dynamically checks schema tables and auto-adds password hashing support column (SQLite / PostgreSQL)."""
    from sqlalchemy import text
    from api.database import AsyncSessionLocal
    
    print("[Startup] Scanning database schema constraints...")
    async with AsyncSessionLocal() as session:
        try:
            dialect_name = session.bind.dialect.name
            if dialect_name == "sqlite":
                # Raw SQLite schema verification
                await session.execute(text("PRAGMA foreign_keys=OFF;"))
                res = await session.execute(text("PRAGMA table_info(users);"))
                columns = [r[1] for r in res.fetchall()]
                if "hashed_password" not in columns:
                    print("[Migration] Adding hashed_password column to SQLite users table...")
                    await session.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NULL;"))
                    await session.commit()
            elif dialect_name == "postgresql":
                # PostgreSQL schema verification
                res = await session.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='users' AND column_name='hashed_password';"
                ))
                if not res.fetchone():
                    print("[Migration] Adding hashed_password column to PostgreSQL users table...")
                    await session.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NULL;"))
                    # Alter clerk_user_id to be nullable in PostgreSQL
                    await session.execute(text("ALTER TABLE users ALTER COLUMN clerk_user_id DROP NOT NULL;"))
                    await session.commit()
        except Exception as e:
            print(f"[Migration] Auto-migration check warning: {e}")

    # Seed default tenant prospects at startup if empty to eliminate first-load lazy sync delays
    try:
        from api.sync import sync_dol_data
        from api.database import SessionLocal
        from api.models import Prospect
        
        sync_db = SessionLocal()
        try:
            count = sync_db.query(Prospect).filter_by(tenant_id="default_tenant").count()
            if count == 0:
                print("[Startup] Default tenant prospects database is empty. Pre-seeding prospects...")
                sync_dol_data(sync_db, target_tenant_id="default_tenant")
                print("[Startup] Pre-seeding completed.")
            else:
                print("[Startup] Default tenant prospects already seeded.")
        finally:
            sync_db.close()
    except Exception as e:
        print(f"[Startup] Seeding prospects warning: {e}")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(prospects.router, prefix="/api/v1/prospects", tags=["Prospects"])
app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["Discovery"])
app.include_router(audits.router, prefix="/api/v1/audits", tags=["Audits"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])

@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "healthy",
        "environment": config.ENVIRONMENT,
        "database": "connected" if config.DATABASE_URL else "not configured"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
