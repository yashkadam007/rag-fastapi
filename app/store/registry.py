from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app import config
from app.lib.db import SessionLocal
from app.store.models import Document


Record = Dict[str, object]


class JsonRegistry:
    """Original JSON registry implementation kept for fallback/rollback."""

    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read(self) -> List[Record]:
        text = self.path.read_text(encoding="utf-8")
        try:
            data = json.loads(text) if text.strip() else []
        except json.JSONDecodeError:
            data = []
        return data  # type: ignore[return-value]

    def _write(self, rows: List[Record]) -> None:
        self.path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def upsert_file(
        self,
        *,
        file_id: str,
        filename: str,
        size_bytes: int,
        workspace: str,
        num_chunks: int,
        indexed: bool,
    ) -> None:
        rows = self._read()
        now = int(time.time())
        updated = False
        for r in rows:
            if str(r.get("fileId")) == file_id:
                r.update(
                    {
                        "fileId": file_id,
                        "filename": filename,
                        "sizeBytes": size_bytes,
                        "workspace": workspace,
                        "numChunks": num_chunks,
                        "indexed": indexed,
                        "updatedAt": now,
                    }
                )
                updated = True
                break
        if not updated:
            rows.append(
                {
                    "fileId": file_id,
                    "filename": filename,
                    "sizeBytes": size_bytes,
                    "workspace": workspace,
                    "numChunks": num_chunks,
                    "indexed": indexed,
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
        rows.sort(key=lambda r: (int(r.get("createdAt", 0)), str(r.get("fileId", ""))))
        self._write(rows)

    def delete_file(self, file_id: str) -> bool:
        rows = self._read()
        kept: List[Record] = []
        removed = False
        for r in rows:
            if str(r.get("fileId")) == file_id:
                removed = True
            else:
                kept.append(r)
        if removed:
            self._write(kept)
        return removed

    def get(self, file_id: str) -> Optional[Record]:
        for r in self._read():
            if str(r.get("fileId")) == file_id:
                return r
        return None


class Registry:
    """Postgres-backed registry with transparent JSON fallback when enabled."""

    def __init__(self, path: Path) -> None:
        self._json = JsonRegistry(path)

    async def upsert_file(
        self,
        *,
        file_id: str,
        filename: str,
        size_bytes: int,
        workspace: str,
        num_chunks: int,
        indexed: bool,
    ) -> None:
        if config.USE_JSON_REGISTRY or not config.DATABASE_URL:
            self._json.upsert_file(
                file_id=file_id,
                filename=filename,
                size_bytes=size_bytes,
                workspace=workspace,
                num_chunks=num_chunks,
                indexed=indexed,
            )
            return

        now = int(time.time())
        async with SessionLocal() as session:
            stmt = insert(Document).values(
                file_id=file_id,
                filename=filename,
                size_bytes=size_bytes,
                workspace=workspace,
                num_chunks=num_chunks,
                indexed=indexed,
                created_at=now,
                updated_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Document.file_id],
                set_={
                    "filename": filename,
                    "size_bytes": size_bytes,
                    "workspace": workspace,
                    "num_chunks": num_chunks,
                    "indexed": indexed,
                    "updated_at": now,
                },
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_file(self, file_id: str) -> bool:
        if config.USE_JSON_REGISTRY or not config.DATABASE_URL:
            return self._json.delete_file(file_id)
        async with SessionLocal() as session:
            stmt = delete(Document).where(Document.file_id == file_id)
            result = await session.execute(stmt)
            await session.commit()
            rows = result.rowcount or 0
            return rows > 0

    async def get(self, file_id: str) -> Optional[Record]:
        if config.USE_JSON_REGISTRY or not config.DATABASE_URL:
            return self._json.get(file_id)
        async with SessionLocal() as session:
            stmt = select(Document).where(Document.file_id == file_id)
            res = await session.execute(stmt)
            doc: Optional[Document] = res.scalar_one_or_none()
            if not doc:
                return None
            return {
                "fileId": doc.file_id,
                "filename": doc.filename,
                "sizeBytes": int(doc.size_bytes),
                "workspace": doc.workspace,
                "numChunks": int(doc.num_chunks),
                "indexed": bool(doc.indexed),
                "createdAt": int(doc.created_at),
                "updatedAt": int(doc.updated_at),
            }
