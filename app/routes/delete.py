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
    file_id = payload.get("fileId")
    if not file_id:
        raise HTTPException(status_code=400, detail="fileId is required")

    removed = vec_store.delete_by_file_id(str(file_id))
    registry.delete_file(str(file_id))

    return {"ok": True, "removed": removed}
