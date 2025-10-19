from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app import config
from app.lib.chunker import chunk_text
from app.lib.embeddings import embed_texts
from app.lib.parsers import parse_from_bytes
from app.store.registry import Registry
from app.store.vector_store import VectorStore


registry = Registry(config.REGISTRY_PATH)
vec_store = VectorStore(config.VEC_PATH)


def generate_file_id() -> str:
    """Generate a unique file id."""
    return uuid.uuid4().hex


async def ingest_document(
    *,
    filename: str,
    data: bytes,
    workspace: Optional[str] = None,
    file_id: Optional[str] = None,
    size_bytes: Optional[int] = None,
) -> Dict[str, object]:
    """Run the shared ingestion pipeline: parse → chunk → embed → upsert → registry.

    Returns a response dict: { ok, fileId, chunks, workspace }.
    """
    workspace_value = (workspace or config.DEFAULT_WORKSPACE).strip() or config.DEFAULT_WORKSPACE

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
    assigned_file_id = file_id or generate_file_id()
    rows: List[dict] = []
    for idx, (chunk_text_value, embedding) in enumerate(zip(chunks, embeddings)):
        row = {
            "id": f"{assigned_file_id}:{idx}",
            "fileId": assigned_file_id,
            "filename": filename,
            "chunkId": idx,
            "workspace": workspace_value,
            "text": chunk_text_value,
            "embedding": embedding,
            "createdAt": created_at,
        }
        rows.append(row)

    upserted = vec_store.upsert(rows)

    # Update registry (async)
    await registry.upsert_file(
        file_id=assigned_file_id,
        filename=filename,
        size_bytes=actual_size,
        workspace=workspace_value,
        num_chunks=len(rows),
        indexed=True,
    )

    return {"ok": True, "fileId": assigned_file_id, "chunks": upserted, "workspace": workspace_value}
