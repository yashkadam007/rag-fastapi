from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app import config
from app.lib.chunker import chunk_text
from app.lib.embeddings import embed_texts
from app.lib.parsers import parse_from_bytes
from app.store.vector_store import VectorStore
from app.lib.db import SessionLocal
from app.store.models import Document


vec_store = VectorStore(config.VEC_PATH)


def generate_document_id() -> str:
    """Generate a unique document id as a UUIDv4 string (with hyphens)."""
    return str(uuid.uuid4())


async def ingest_document(
    *,
    filename: str,
    data: bytes,
    chat_id: str,
    uploader_user_id: str,
    document_id: Optional[str] = None,
    size_bytes: Optional[int] = None,
) -> Dict[str, object]:
    """Parse → chunk → embed → upsert chunks; create Document if DB is enabled.

    Returns: { ok, documentId, chunks }
    """

    # Validate size limit
    actual_size = size_bytes if size_bytes is not None else len(data)
    if actual_size > config.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max {config.MAX_UPLOAD_MB}MB.",
        )

    # Parse
    text = parse_from_bytes(filename=filename, content_type=None, data=data)

    # Chunk
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="No text to index.")

    # Embed
    embeddings = embed_texts(chunks)

    # Upsert into vector store
    created_at = int(time.time())
    assigned_document_id = document_id or generate_document_id()
    rows: List[dict] = []
    for idx, (chunk_text_value, embedding) in enumerate(zip(chunks, embeddings)):
        row = {
            "id": str(uuid.uuid4()),
            "documentId": assigned_document_id,
            "chunkId": idx,
            "text": chunk_text_value,
            "embedding": embedding,
            "createdAt": created_at,
            "chatId": chat_id,
        }
        rows.append(row)

    upserted = await vec_store.upsert(rows)

    # Persist Document in DB when available
    if SessionLocal:
        async with SessionLocal() as session:  # type: ignore[arg-type]
            doc = Document(
                id=uuid.UUID(assigned_document_id),
                chat_id=uuid.UUID(chat_id),
                uploader_user_id=uuid.UUID(uploader_user_id),
                filename=filename,
                mime_type=None,
                size_bytes=actual_size,
                storage_key=None,
                num_chunks=len(rows),
                indexed=True,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(doc)
            await session.commit()

    return {"ok": True, "documentId": assigned_document_id, "chunks": upserted}
