from __future__ import annotations

import base64
import hashlib
import os
import time
import uuid
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app.lib.db import SessionLocal
from app.store.models import Session as DbSession, User


_pwd_ctx = CryptContext(schemes=[config.PASSWORD_HASH_SCHEME], deprecated="auto")


def hash_password(plain_password: str) -> str:
    if not plain_password or len(plain_password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return _pwd_ctx.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _pwd_ctx.verify(plain_password, password_hash)
    except Exception:
        return False


def generate_session_token() -> str:
    return base64.urlsafe_b64encode(os.urandom(config.SESSION_TOKEN_BYTES)).decode("ascii").rstrip("=")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(user_id: uuid.UUID, user_agent: Optional[str], ip_address: Optional[str]) -> tuple[str, DbSession]:
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    token = generate_session_token()
    token_hash = hash_token(token)
    now = int(time.time())
    expires_at = now + int(config.SESSION_TTL_SECONDS)
    async with SessionLocal() as session:  # type: ignore[arg-type]
        db_sess = DbSession(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
        )
        session.add(db_sess)
        await session.commit()
        return token, db_sess


async def revoke_session(token: str) -> None:
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    token_hash = hash_token(token)
    async with SessionLocal() as session:  # type: ignore[arg-type]
        stmt = (
            update(DbSession)
            .where(DbSession.token_hash == token_hash, DbSession.revoked_at.is_(None))
            .values(revoked_at=int(time.time()))
        )
        await session.execute(stmt)
        await session.commit()


async def get_current_user(
    request: Request,
    session_cookie: Optional[str] = Cookie(default=None, alias=config.SESSION_COOKIE_NAME),
) -> str:
    """Resolve the authenticated user from session cookie.

    Returns the user_id string if valid; raises 401 otherwise.
    """
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_hash = hash_token(session_cookie)
    now = int(time.time())
    async with SessionLocal() as session:  # type: ignore[arg-type]
        stmt = select(DbSession).where(
            DbSession.token_hash == token_hash,
            DbSession.revoked_at.is_(None),
            DbSession.expires_at > now,
        )
        res = await session.execute(stmt)
        sess: Optional[DbSession] = res.scalars().first()
        if not sess:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Optional: extend sliding expiration
        return str(sess.user_id)

