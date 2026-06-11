import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import config

DATABASE_URL = config.DATABASE_URL

# For async SQLAlchemy: postgresql://... needs to be postgresql+asyncpg://...
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite:///"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

is_sqlite = DATABASE_URL.startswith("sqlite")

# Synchronous engine and session (for scripts, celery, or basic fallback)
if is_sqlite:
    sqlite_db_path = DATABASE_URL.replace("sqlite:///", "")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous engine and session (for async FastAPI endpoints)
if "sqlite+aiosqlite" in ASYNC_DATABASE_URL:
    async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Optimize SQLite performance with WAL and synchronous NORMAL
from sqlalchemy import event

if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    @event.listens_for(async_engine.sync_engine, "connect")
    def set_sqlite_pragma_async(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

Base = declarative_base()

# FastAPI DB Session Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
