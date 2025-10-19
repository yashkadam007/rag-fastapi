from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app import config


def _build_engine() -> Optional[AsyncEngine]:
    if not config.DATABASE_URL:
        return None
    return create_async_engine(
        config.DATABASE_URL,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=config.DB_POOL_RECYCLE,
        connect_args={"ssl": True},
    )


engine: Optional[AsyncEngine] = _build_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False) if engine else None


async def check_health() -> bool:
    try:
        if not engine:
            return False
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        return True
    except Exception:
        return False


