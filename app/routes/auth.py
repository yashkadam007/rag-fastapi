from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app import config
from app.lib.auth import create_session, hash_password, verify_password, revoke_session
from app.lib.db import SessionLocal
from app.store.models import Account, User
from app.lib.auth import get_current_user


router = APIRouter()


@router.post("/auth/sign-up")
async def sign_up(payload: dict, request: Request, response: Response):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    name = (payload.get("name") or "").strip() or None
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")
    if "@" not in email:
        raise HTTPException(status_code=400, detail="invalid email")
    try:
        password_hash = hash_password(password)
    except ValueError as e:
        # Normalize auth lib validation into a client-friendly 400.
        raise HTTPException(status_code=400, detail=str(e))
    now = int(time.time())
    async with SessionLocal() as session:  # type: ignore[arg-type]
        # check existing user by email
        res = await session.execute(select(User).where(User.email == email))
        if res.scalars().first() is not None:
            raise HTTPException(status_code=409, detail="account already exists")
        user = User(id=uuid.uuid4(), auth0_sub=None, email=email, name=name, created_at=now, updated_at=now)
        session.add(user)
        acc = Account(
            id=uuid.uuid4(),
            user_id=user.id,
            password_hash=password_hash,
            email_verified=False,
            created_at=now,
            updated_at=now,
        )
        session.add(acc)
        try:
            await session.commit()
        except IntegrityError:
            # Handles race conditions on unique indexes (e.g. email).
            await session.rollback()
            raise HTTPException(status_code=409, detail="account already exists")

    token, _ = await create_session(user.id, request.headers.get("user-agent"), request.client.host if request.client else None)
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=config.SESSION_TTL_SECONDS,
        path="/",
    )
    return {"ok": True, "userId": str(user.id), "email": email, "name": name}


@router.post("/auth/sign-in")
async def sign_in(payload: dict, request: Request, response: Response):
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")
    async with SessionLocal() as session:  # type: ignore[arg-type]
        # find user by email
        res_user = await session.execute(select(User).where(User.email == email))
        user: Optional[User] = res_user.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="invalid credentials")
        # load account by user_id
        res_acc = await session.execute(select(Account).where(Account.user_id == user.id))
        acc: Optional[Account] = res_acc.scalars().first()
        if not acc or not verify_password(password, acc.password_hash):
            raise HTTPException(status_code=401, detail="invalid credentials")
    token, _ = await create_session(user.id, request.headers.get("user-agent"), request.client.host if request.client else None)
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=config.SESSION_TTL_SECONDS,
        path="/",
    )
    return {"ok": True, "userId": str(user.id), "email": user.email, "name": user.name}


@router.post("/auth/sign-out")
async def sign_out(response: Response, session_cookie: Optional[str] = Cookie(default=None, alias=config.SESSION_COOKIE_NAME)):
    if session_cookie:
        await revoke_session(session_cookie)
    response.delete_cookie(key=config.SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/auth/me")
async def me(user_id: str = Depends(get_current_user)):
    return {"ok": True, "userId": user_id}


