from __future__ import annotations

import time
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.lib.auth import require_user_id
from app.lib.db import SessionLocal
from app.store.models import Chat, Document, Message
from app.store.models import Chunk
from sqlalchemy import delete, select


router = APIRouter()


@router.post("/chats")
async def create_chat(payload: dict, user_id: str = Depends(require_user_id)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    title = (payload.get("title") or "Untitled").strip() or "Untitled"
    now = int(time.time())
    async with SessionLocal() as session:  # type: ignore[arg-type]
        chat = Chat(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            title=title,
            created_at=now,
            updated_at=now,
        )
        session.add(chat)
        await session.commit()
        return {
            "id": str(chat.id),
            "title": chat.title,
            "createdAt": chat.created_at,
            "updatedAt": chat.updated_at,
        }


@router.get("/chats")
async def list_chats(user_id: str = Depends(require_user_id)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    async with SessionLocal() as session:  # type: ignore[arg-type]
        stmt = select(Chat).where(Chat.user_id == uuid.UUID(user_id)).order_by(Chat.created_at.desc())
        res = await session.execute(stmt)
        chats: List[Chat] = list(res.scalars().all())
        return [
            {
                "id": str(c.id),
                "title": c.title,
                "createdAt": c.created_at,
                "updatedAt": c.updated_at,
            }
            for c in chats
        ]


@router.get("/chats/{chat_id}")
async def get_chat(chat_id: str, user_id: str = Depends(require_user_id)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    async with SessionLocal() as session:  # type: ignore[arg-type]
        chat = await session.get(Chat, uuid.UUID(chat_id))
        if not chat or str(chat.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {
            "id": str(chat.id),
            "title": chat.title,
            "createdAt": chat.created_at,
            "updatedAt": chat.updated_at,
        }


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user_id: str = Depends(require_user_id)):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    chat_uuid = uuid.UUID(chat_id)
    async with SessionLocal() as session:  # type: ignore[arg-type]
        chat = await session.get(Chat, chat_uuid)
        if not chat or str(chat.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Chat not found")
        # Delete messages in chat
        await session.execute(delete(Message).where(Message.chat_id == chat_uuid))
        # Find documents in chat
        res = await session.execute(select(Document.id).where(Document.chat_id == chat_uuid))
        doc_ids = [row[0] for row in res.all()]
        # Delete chunks for documents
        for did in doc_ids:
            await session.execute(delete(Chunk).where(Chunk.document_id == did))
        # Delete documents
        await session.execute(delete(Document).where(Document.chat_id == chat_uuid))
        # Delete chat
        await session.delete(chat)
        await session.commit()
        return {"ok": True}


