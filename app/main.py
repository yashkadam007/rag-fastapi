from __future__ import annotations

from fastapi import FastAPI

from app.lib.logger import request_logging_middleware
from app.lib import db as db_module
from app.routes.chats import router as chats_router
from app.routes.documents import router as documents_router
from app.routes.messages import router as messages_router

app = FastAPI()

# Lightweight request logging
app.middleware("http")(request_logging_middleware)


@app.get("/health")
async def health():
    db_ok = await db_module.check_health() if db_module else False
    return {"ok": True, "db": db_ok}

# Include routes
app.include_router(chats_router)
app.include_router(documents_router)
app.include_router(messages_router)
