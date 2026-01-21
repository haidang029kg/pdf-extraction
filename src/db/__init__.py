import contextlib
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.core.settings import settings

async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=settings.debug,
    pool_size=settings.pool_size,
    max_overflow=settings.max_overflow,
)


async def connect_db():
    from sqlalchemy import text

    async with async_engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        result.scalar()


@contextlib.asynccontextmanager
async def get_async_session_ctx() -> AsyncGenerator[AsyncSession, Any]:
    async with AsyncSession(async_engine) as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, Any]:
    async with AsyncSession(async_engine) as session:
        yield session


__all__ = [
    "get_async_session",
    "get_async_session_ctx",
]
