# Migration: JSON registry to Neon Postgres (SQLAlchemy async + Alembic)

This runbook migrates the registry from `data/registry.json` to Neon Postgres using SQLAlchemy 2.0 (async) with asyncpg and Alembic.

## Prerequisites
- Neon Postgres database and credentials
- Python 3.11+
- `DATABASE_URL` like: `postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require`

## Configure
Create/update `.env`:
```
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=300
# Optional rollback flag:
USE_JSON_REGISTRY=false
```

Install deps:
```
pip install -r requirements.txt
```

## Apply migrations
Alembic files are in `alembic/`. Ensure `DATABASE_URL` is exported in the shell or present in `.env`.

Run upgrade to head:
```
alembic upgrade head
```

Verify schema:
```
alembic history
```

## Deploy
1. Set `DATABASE_URL` in environment/secrets for the service.
2. Deploy the application.
3. Check health:
```
curl -s http://localhost:8000/health
```
Expected response:
```
{"ok": true, "db": true}
```

## Verification
- Ingest a file via `/ingest/file` or `/ingest/url`.
- Confirm document row in Postgres (`documents` table) and vectors persisted to `data/vec.json` (unchanged).
- Ask a question via `/ask` and confirm sources reference ingested file.
- Delete via `/delete` and confirm registry row removed and vectors deleted.

## Rollback
No code changes required. Flip to JSON registry storage:
```
export USE_JSON_REGISTRY=true
```
Restart the service. The app will use `data/registry.json` for registry operations.

## Operational notes
- Connection pooling is configured with `pool_pre_ping` and recycle to handle Neon idling.
- Health endpoint includes DB connectivity probe.
- Least privilege: grant app DB user only DML on `documents` (CREATE/DROP not required after migration).

## Common issues
- `Missing DATABASE_URL`: set it in `.env` or environment.
- `db: false` in `/health`: database unreachable or SSL required; ensure `?sslmode=require`.
- Alembic not found: `pip install alembic` or ensure venv is active.


