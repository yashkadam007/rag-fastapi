from __future__ import annotations

import time
import uuid
from typing import List, Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException

from app import config
from app.lib.auth import get_current_user
from app.lib.embeddings import embed_query
from app.lib.db import SessionLocal
from app.store.models import Message
from app.store.vector_store import VectorStore


router = APIRouter()


@router.get("/chats/{chat_id}/messages")
async def list_messages(chat_id: str, limit: Optional[int] = None, before: Optional[int] = None, user_id: str = Depends(get_current_user)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    from sqlalchemy import select
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatId")
    async with SessionLocal() as session:  # type: ignore[arg-type]
        stmt = select(Message).where(Message.chat_id == chat_uuid)
        if before is not None:
            stmt = stmt.where(Message.created_at < int(before))
        stmt = stmt.order_by(Message.created_at.desc())
        if limit is not None:
            stmt = stmt.limit(max(1, int(limit)))
        res = await session.execute(stmt)
        msgs: List[Message] = list(res.scalars().all())
        msgs.reverse()  # return ascending by time for UI convenience
        return [
            {"id": str(m.id), "role": m.role, "content": m.content, "createdAt": int(m.created_at)}
            for m in msgs
        ]


@router.post("/chats/{chat_id}/messages")
async def add_user_message(chat_id: str, payload: dict, user_id: str = Depends(get_current_user)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    content: str = (payload.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatId")
    now = int(time.time())
    async with SessionLocal() as session:  # type: ignore[arg-type]
        msg = Message(
            id=uuid.uuid4(),
            chat_id=chat_uuid,
            role="user",
            content=content,
            tokens_in=None,
            tokens_out=None,
            meta=None,
            created_at=now,
        )
        session.add(msg)
        await session.commit()
        return {"id": str(msg.id), "role": msg.role, "content": msg.content, "createdAt": msg.created_at}


@router.post("/chats/{chat_id}/ask")
async def ask(chat_id: str, payload: dict, user_id: str = Depends(get_current_user)):
    q: str = (payload.get("q") or "").strip()
    k: int = int(payload.get("k") or 15)
    if not q:
        raise HTTPException(status_code=400, detail="q is required")
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatId")

    # Write user message
    user_msg = await add_user_message(chat_id, {"content": q}, user_id)  # type: ignore[arg-type]

    vec_store = VectorStore(config.VEC_PATH)
    q_vec = embed_query(q)
    results = await vec_store.search(q_vec, chat_id=str(chat_uuid), k=k)

    context_items = results[:8]
    context_texts: List[str] = []
    for row, score in context_items:
        text: str = str(row.get("text", ""))
        context_texts.append(text)

    if not context_texts:
        answer = "I couldn't find relevant context."
        sources: List[dict] = []
    else:
        genai.configure(api_key=config.GOOGLE_API_KEY)
        if not config.GOOGLE_API_KEY:
            raise HTTPException(status_code=400, detail="Missing GOOGLE_API_KEY. Please set it in the environment.")
        prompt = (
            "You are a helpful assistant. Answer the question using ONLY the provided context. "
            "If unknown, say you don't know.\n\n"
            f"Question: {q}\n\n"
            "Context:\n" + "\n---\n".join(context_texts)
        )
        try:
            model = genai.GenerativeModel(config.GENERATION_MODEL)
            resp = model.generate_content(prompt)
            answer = resp.text.strip() if getattr(resp, "text", None) else ""
            if not answer:
                raise HTTPException(status_code=502, detail="Model returned empty response.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail="Failed to generate an answer.")
        sources = [
            {"filename": str(r[0].get("filename")), "chunkId": int(r[0].get("chunkId", 0))}
            for r in context_items
        ]

    # Persist assistant message
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    now = int(time.time())
    async with SessionLocal() as session:  # type: ignore[arg-type]
        msg = Message(
            id=uuid.uuid4(),
            chat_id=uuid.UUID(chat_id),
            role="assistant",
            content=answer,
            tokens_in=None,
            tokens_out=None,
            meta=None,
            created_at=now,
        )
        session.add(msg)
        await session.commit()

    return {"answer": answer, "sources": sources}


