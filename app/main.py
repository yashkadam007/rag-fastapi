from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from app.lib.logger import request_logging_middleware
from app.lib import db as db_module
from app.routes.chats import router as chats_router
from app.routes.documents import router as documents_router
from app.routes.messages import router as messages_router
from app.routes.auth import router as auth_router

app = FastAPI()

# Lightweight request logging
app.middleware("http")(request_logging_middleware)

def _parse_cors_origins(value: str) -> list[str]:
    """Parse CORS origins from env.

    Supports:
    - Comma-separated list: "https://a.com,https://b.com"
    - JSON array: '["https://a.com","https://b.com"]'
    """
    raw = value.strip()
    if not raw:
        return []

    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass

    return [part.strip() for part in raw.split(",") if part.strip()]

_cors_origins = _parse_cors_origins(os.getenv("CORS_ORIGINS", ""))
_cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", "").strip() or None

# Defaults for local development if CORS_ORIGINS is not set.
allow_origins = _cors_origins or [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    db_ok = await db_module.check_health() if db_module else False
    return {"ok": True, "db": db_ok}

# Include routes
app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(documents_router)
app.include_router(messages_router)
