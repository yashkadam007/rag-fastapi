from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import config
from app.store.registry import Registry
from app.store.vector_store import VectorStore

router = APIRouter()

vec_store = VectorStore(config.VEC_PATH)
registry = Registry(config.REGISTRY_PATH)


@router.post("/delete")
async def delete(payload: dict):
    # Legacy endpoint retained as no-op in chat-scoped v0
    return {"ok": True, "removed": 0}
