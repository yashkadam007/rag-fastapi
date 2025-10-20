from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config
from alembic import context

# Ensure project root on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.store.models import Base  # single declarative Base lives in models.py
from app.store import models as _models  # ensure models module imported (registers tables)

config_obj = context.config

# Resolve DB URL from env (required)
db_url = os.getenv("DATABASE_URL")
if db_url:
    config_obj.set_main_option("sqlalchemy.url", db_url)
url_opt = config_obj.get_main_option("sqlalchemy.url")
if not url_opt or "%(" in url_opt or url_opt.strip().lower() in ("", "none"):
    raise RuntimeError("DATABASE_URL is not set/invalid for Alembic. Export it and retry.")

target_metadata = Base.metadata
if not target_metadata.tables:
    raise RuntimeError("No tables found in Base.metadata. Ensure app.store.models defines models and is imported.")

def run_migrations_offline() -> None:
    url = config_obj.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable: AsyncEngine = async_engine_from_config(
        config_obj.get_section(config_obj.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())