from collections.abc import AsyncGenerator

from sqlalchemy.engine.url import make_url
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
    1. Converts 'postgres://' or 'postgresql://' scheme to 'postgresql+asyncpg://'.
    2. Strips libpq-only parameters not accepted by asyncpg (channel_binding, sslmode, gssencmode, etc.).
    3. Configures ssl=require if SSL was specified in the original query.
    """
    if not raw_url:
        return ""
    url_str = raw_url.strip()
    if url_str.startswith("postgres://"):
        url_str = url_str.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url_str.startswith("postgresql://") and not url_str.startswith("postgresql+asyncpg://"):
        url_str = url_str.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed_url = make_url(url_str)
    unsupported_keys = {
        "channel_binding",
        "sslmode",
        "gssencmode",
        "target_session_attrs",
        "options",
    }

    query_dict = dict(parsed_url.query)
    has_ssl = "ssl" in query_dict or query_dict.get("sslmode") in (
        "require",
        "verify-ca",
        "verify-full",
        "prefer",
    )

    for key in list(query_dict.keys()):
        if key in unsupported_keys:
            del query_dict[key]

    if has_ssl:
        query_dict["ssl"] = "require"

    cleaned_url = parsed_url._replace(query=query_dict)
    return cleaned_url.render_as_string(hide_password=False)


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