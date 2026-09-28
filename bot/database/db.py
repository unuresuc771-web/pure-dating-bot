from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from bot.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from sqlalchemy import text
        for col, col_type in [
            ("couple_age", "VARCHAR(32)"),
            ("is_fake", "BOOLEAN DEFAULT 0"),
            ("last_seen_at", "TIMESTAMP"),
            ("total_active_seconds", "INTEGER DEFAULT 0"),
            ("personal_password", "VARCHAR(64) DEFAULT NULL"),
            ("referrer_id", "INTEGER DEFAULT NULL"),
            ("referral_count", "INTEGER DEFAULT 0"),
            ("utm_source", "VARCHAR(64) DEFAULT NULL")
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type};"))
            except Exception:
                pass

async def get_db_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
