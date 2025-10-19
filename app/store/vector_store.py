from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np


Row = Dict[str, object]


class VectorStore:
    """JSON-file vector store for embeddings and chunks."""

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
        """Insert or replace rows by unique id. Returns number of rows upserted."""
        existing = self._read()
        by_id: Dict[str, Row] = {str(r["id"]): r for r in existing if "id" in r}
        count = 0
        for row in rows:
            row_id = str(row.get("id"))
            by_id[row_id] = row
            count += 1
        # Stable order: sort by createdAt then id for determinism
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
        """Return top-k rows and scores in the given workspace.

        Deterministic ordering: score desc, tie-breaker by id asc.
        """
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
        # Sort deterministically
        candidates.sort(key=lambda rs: (-rs[1], str(rs[0].get("id", ""))))
        return candidates[: max(0, k)]
