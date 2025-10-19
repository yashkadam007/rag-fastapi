from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional


Record = Dict[str, object]


class Registry:
    """JSON registry for ingested files and indexing metadata."""

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
