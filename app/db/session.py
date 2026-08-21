from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.models import Base


def _normalize_database_url(raw_url: str) -> str:
    """
    Normalizes PostgreSQL connection strings for asyncpg and cloud providers (Neon/Render).
    Converts 'postgres://' or 'postgresql://' to 'postgresql+asyncpg://' and
    translates 'sslmode=require' query parameters to 'ssl=require'.
    """
    if not raw_url:
        return ""
    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")
    return url


# create_async_engine with NullPool to prevent event loop connection conflicts in async environments
engine = create_async_engine(
    _normalize_database_url(settings.database_url),
    echo=False,
    pool_pre_ping=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Bootstraps schema tables on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for scoped database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise