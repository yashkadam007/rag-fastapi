from __future__ import annotations

from typing import List

CHUNK_SIZE = 3500
CHUNK_OVERLAP = 600


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into chunks with overlap.

    Ensures chunks are around `chunk_size` characters with `overlap` between
    adjacent chunks. Returns a list of chunk strings.
    """
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks
