from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app import config
from app.lib.db import SessionLocal
from app.store.vector_models import Chunk


Row = Dict[str, object]


class JsonVectorStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read(self) -> List[Row]:
        text = self.path.read_text(encoding="utf-8")
        try:
            data = json.loads(text) if text.strip() else []
        except json.JSONDecodeError:
            data = []
        if not isinstance(data, list):
            data = []
        return data  # type: ignore[return-value]

    def _write(self, rows: List[Row]) -> None:
        self.path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def upsert(self, rows: Iterable[Row]) -> int:
        existing = self._read()
        by_id: Dict[str, Row] = {str(r["id"]): r for r in existing if "id" in r}
        count = 0
        for row in rows:
            row_id = str(row.get("id"))
            by_id[row_id] = row
            count += 1
        merged = list(by_id.values())
        merged.sort(key=lambda r: (int(r.get("createdAt", 0)), str(r.get("id", ""))))
        self._write(merged)
        return count

    def delete_by_file_id(self, file_id: str) -> int:
        rows = self._read()
        kept: List[Row] = []
        removed = 0
        for r in rows:
            if str(r.get("fileId")) == file_id:
                removed += 1
            else:
                kept.append(r)
        self._write(kept)
        return removed

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        if a.size == 0 or b.size == 0:
            return 0.0
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0.0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def search(self, query_vec: List[float], *, workspace: str, k: int = 15) -> List[Tuple[Row, float]]:
        rows = self._read()
        q = np.array(query_vec, dtype=np.float32)
        candidates: List[Tuple[Row, float]] = []
        for r in rows:
            if str(r.get("workspace")) != workspace:
                continue
            emb = r.get("embedding")
            if not isinstance(emb, list):
                continue
            v = np.array(emb, dtype=np.float32)
            score = self._cosine(q, v)
            candidates.append((r, score))
        candidates.sort(key=lambda rs: (-rs[1], str(rs[0].get("id", ""))))
        return candidates[: max(0, k)]


class VectorStore:
    """Pgvector-backed vector store with JSON fallback by feature flag."""

    def __init__(self, path: Path) -> None:
        self._json = JsonVectorStore(path)

    async def upsert(self, rows: Iterable[Row]) -> int:
        if config.USE_JSON_VECTOR_STORE or not SessionLocal:
            return self._json.upsert(rows)
        values = [
            {
                "id": r["id"],
                "file_id": r["fileId"],
                "filename": r["filename"],
                "chunk_id": r["chunkId"],
                "workspace": r["workspace"],
                "text": r["text"],
                "embedding": r["embedding"],
                "created_at": r["createdAt"],
            }
            for r in rows
        ]
        if not values:
            return 0
        async with SessionLocal() as session:  # type: ignore[arg-type]
            stmt = pg_insert(Chunk).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Chunk.id],
                set_={
                    "file_id": stmt.excluded.file_id,
                    "filename": stmt.excluded.filename,
                    "chunk_id": stmt.excluded.chunk_id,
                    "workspace": stmt.excluded.workspace,
                    "text": stmt.excluded.text,
                    "embedding": stmt.excluded.embedding,
                    "created_at": stmt.excluded.created_at,
                },
            )
            await session.execute(stmt)
            await session.commit()
            return len(values)

    async def delete_by_file_id(self, file_id: str) -> int:
        if config.USE_JSON_VECTOR_STORE or not SessionLocal:
            return self._json.delete_by_file_id(file_id)
        async with SessionLocal() as session:  # type: ignore[arg-type]
            result = await session.execute(delete(Chunk).where(Chunk.file_id == file_id))
            await session.commit()
            return int(result.rowcount or 0)

    async def search(self, query_vec: List[float], *, workspace: str, k: int = 15) -> List[Tuple[Row, float]]:
        if config.USE_JSON_VECTOR_STORE or not SessionLocal:
            return self._json.search(query_vec, workspace=workspace, k=k)
        async with SessionLocal() as session:  # type: ignore[arg-type]
            # Cosine distance ascending → smallest distance = best match
            stmt = (
                select(Chunk, Chunk.embedding.cosine_distance(query_vec).label("distance"))
                .where(Chunk.workspace == workspace)
                .order_by("distance")
                .limit(max(0, k))
            )
            res = await session.execute(stmt)
            pairs: List[Tuple[Row, float]] = []
            for row, distance in res.all():
                out: Row = {
                    "id": row.id,
                    "fileId": row.file_id,
                    "filename": row.filename,
                    "chunkId": row.chunk_id,
                    "workspace": row.workspace,
                    "text": row.text,
                }
                # Convert distance to similarity for caller parity with JSON cosine
                sim = 1.0 - float(distance)
                pairs.append((out, sim))
            return pairs
