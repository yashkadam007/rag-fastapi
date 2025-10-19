from __future__ import annotations

from typing import List

import google.generativeai as genai
from fastapi import HTTPException, status

from app import config


def _ensure_api_key() -> None:
    if not config.GOOGLE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing GOOGLE_API_KEY. Please set it in the environment.",
        )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts into vector embeddings.

    Raises an HTTPException with friendly message if the API key is missing.
    """
    _ensure_api_key()
    genai.configure(api_key=config.GOOGLE_API_KEY)

    results: List[List[float]] = []
    for t in texts:
        try:
            if not t.strip():
                results.append([])
                continue
            res = genai.embed_content(model=config.EMBEDDING_MODEL, content=t)
            vec = res.get("embedding") or res.get("data", [{}])[0].get("embedding")
            if not vec:
                raise HTTPException(status_code=500, detail="Failed to embed content.")
            results.append(vec)  # type: ignore[arg-type]
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Embedding service error.")
    return results


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    vecs = embed_texts([text])
    return vecs[0]
