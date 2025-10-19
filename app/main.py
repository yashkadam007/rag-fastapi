from __future__ import annotations

from fastapi import FastAPI

from app.lib.logger import request_logging_middleware
from app.routes.ask import router as ask_router
from app.routes.delete import router as delete_router
from app.routes.ingest import router as ingest_router

app = FastAPI()

# Lightweight request logging
app.middleware("http")(request_logging_middleware)


@app.get("/health")
async def health():
    return {"ok": True}

# Include routes
app.include_router(ingest_router)
app.include_router(ask_router)
app.include_router(delete_router)
