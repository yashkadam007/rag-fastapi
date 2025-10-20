from __future__ import annotations

import uuid
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app import config
from app.lib.auth import require_user_id
from app.lib.pipeline import ingest_document
from app.lib.db import SessionLocal
from app.store.models import Document
from sqlalchemy import delete, select


router = APIRouter()


@router.get("/chats/{chat_id}/documents")
async def list_documents(chat_id: str, user_id: str = Depends(require_user_id)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    async with SessionLocal() as session:  # type: ignore[arg-type]
        stmt = select(Document).where(Document.chat_id == uuid.UUID(chat_id))
        res = await session.execute(stmt)
        docs: List[Document] = list(res.scalars().all())
        return [
            {
                "id": str(d.id),
                "filename": d.filename,
                "sizeBytes": int(d.size_bytes),
                "numChunks": int(d.num_chunks),
                "indexed": bool(d.indexed),
                "createdAt": int(d.created_at),
                "updatedAt": int(d.updated_at),
            }
            for d in docs
        ]


@router.post("/chats/{chat_id}/documents/file")
async def upload_file(
    chat_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(require_user_id),
):
    data = await file.read()
    size_bytes = len(data)
    if size_bytes > config.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max {config.MAX_UPLOAD_MB}MB.",
        )
    result = await ingest_document(
        filename=file.filename,
        data=data,
        chat_id=chat_id,
        uploader_user_id=user_id,
        size_bytes=size_bytes,
    )
    return result


@router.post("/chats/{chat_id}/documents/url")
async def ingest_url(chat_id: str, payload: dict, user_id: str = Depends(require_user_id)):
    file_url = payload.get("fileUrl")
    filename = payload.get("filename")
    if not file_url or not filename:
        raise HTTPException(status_code=400, detail="fileUrl and filename are required")
    headers = {"User-Agent": "rag-fastapi/1.0"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            resp = await client.get(file_url, follow_redirects=True)
        except httpx.HTTPError:
            raise HTTPException(status_code=400, detail="Failed to fetch the file URL.")
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch the file URL.")
    data = resp.content
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Max {config.MAX_UPLOAD_MB}MB.")
    result = await ingest_document(
        filename=filename,
        data=data,
        chat_id=chat_id,
        uploader_user_id=user_id,
        size_bytes=len(data),
    )
    return result


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, user_id: str = Depends(require_user_id)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    async with SessionLocal() as session:  # type: ignore[arg-type]
        doc = await session.get(Document, uuid.UUID(document_id))
        if not doc:
            return {"ok": True, "removed": 0}
        # For simplicity in v0, allow deletion if caller owns the parent chat (check omitted; assumed)
        # Delete chunks
        from app.store.vector_store import VectorStore  # avoid cycle at import

        removed = await VectorStore(config.VEC_PATH).delete_by_document_id(document_id)
        await session.execute(delete(Document).where(Document.id == uuid.UUID(document_id)))
        await session.commit()
        return {"ok": True, "removed": int(removed)}


