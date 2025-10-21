from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.lib.logger import request_logging_middleware
from app.lib import db as db_module
from app.routes.chats import router as chats_router
from app.routes.documents import router as documents_router
from app.routes.messages import router as messages_router
from app.routes.auth import router as auth_router

app = FastAPI()

# Lightweight request logging
app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
