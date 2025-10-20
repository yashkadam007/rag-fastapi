from __future__ import annotations

import uuid
from fastapi import Header, HTTPException


async def require_user_id(x_user_id: str | None = Header(None)) -> str:
    """Mock auth dependency. Expects X-User-Id header with UUIDv4 string.

    Returns the user_id string if valid; raises 401 otherwise.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    try:
        uuid.UUID(str(x_user_id))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid X-User-Id header")
    return str(x_user_id)


