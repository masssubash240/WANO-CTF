"""Async SQLAlchemy engine/session management.

Production uses Supabase PostgreSQL through psycopg3; tests may use aiosqlite.
Only the backend holds the service-role credentials — the browser never talks to
this code path directly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


def _create_engine(url: str | None = None) -> AsyncEngine:
    dsn = url or settings.database_url
    kwargs: dict = {"echo": settings.db_echo, "future": True, "pool_pre_ping": True}

    if dsn.startswith("sqlite"):
        # aiosqlite (tests / offline dev)
        kwargs.pop("pool_pre_ping", None)
        return create_async_engine(dsn, **kwargs)

    kwargs.update(
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=1800,  # Supabase pooler drops idle connections
        pool_timeout=30,
    )
    # Supabase transaction pooler (port 6543) cannot use prepared statements.
    if ":6543" in dsn:
        connect_args = {"prepare_threshold": None}
        kwargs["connect_args"] = connect_args
    return create_async_engine(dsn, **kwargs)


engine: AsyncEngine = _create_engine()

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped session."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Programmatic session scope for background tasks / websockets."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    await engine.dispose()


async def check_database() -> bool:
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - health endpoint only
        return False
