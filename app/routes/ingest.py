from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app import config
from app.lib.pipeline import ingest_document

router = APIRouter()


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    workspace: Optional[str] = Form(None),
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
        workspace=workspace,
        size_bytes=size_bytes,
    )
    return result


@router.post("/ingest/url")
async def ingest_url(payload: dict):
    file_url = payload.get("fileUrl")
    filename = payload.get("filename")
    workspace = payload.get("workspace")
    file_id = payload.get("fileId")

    if not file_url or not filename:
        raise HTTPException(status_code=400, detail="fileUrl and filename are required")

    headers = {"User-Agent": "rag-fastapi/1.0"}
    # Optional preflight size check
    size_header_bytes: Optional[int] = None
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            head = await client.head(file_url, follow_redirects=True)
            cl = head.headers.get("Content-Length")
            if cl and cl.isdigit():
                size_header_bytes = int(cl)
                if size_header_bytes > config.MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Max {config.MAX_UPLOAD_MB}MB.",
                    )
        except httpx.HTTPError:
            # Continue; we'll try GET next
            pass
        try:
            resp = await client.get(file_url, follow_redirects=True)
        except httpx.HTTPError:
            raise HTTPException(status_code=400, detail="Failed to fetch the file URL.")

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch the file URL.")

    data = resp.content
    size_bytes = len(data)
    if size_bytes > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Max {config.MAX_UPLOAD_MB}MB.")

    result = await ingest_document(
        filename=filename,
        data=data,
        workspace=workspace,
        file_id=file_id,
        size_bytes=size_bytes,
    )
    return result
