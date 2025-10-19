from __future__ import annotations

from typing import List, Optional

import google.generativeai as genai
from fastapi import APIRouter, HTTPException

from app import config
from app.lib.embeddings import embed_query
from app.store.vector_store import VectorStore
from app.lib.logger import get_logger

router = APIRouter()

vec_store = VectorStore(config.VEC_PATH)
logger = get_logger("rag.ask")


@router.post("/ask")
async def ask(payload: dict):
    q: str = (payload.get("q") or "").strip()
    workspace: str = (payload.get("workspace") or config.DEFAULT_WORKSPACE).strip() or config.DEFAULT_WORKSPACE
    k: int = int(payload.get("k") or 15)

    if not q:
        raise HTTPException(status_code=400, detail="Query 'q' is required")

    q_vec = embed_query(q)
    results = vec_store.search(q_vec, workspace=workspace, k=k)

    # Limit context to top 8 chunks
    context_items = results[:8]
    context_texts: List[str] = []
    citations: List[str] = []
    for row, score in context_items:
        text: str = str(row.get("text", ""))
        filename: str = str(row.get("filename", ""))
        chunk_id: int = int(row.get("chunkId", 0))
        context_texts.append(text)
        citations.append(f"[{filename}#{chunk_id}]")

    if not context_texts:
        return {"answer": "I couldn't find relevant context.", "sources": []}

    genai.configure(api_key=config.GOOGLE_API_KEY)
    if not config.GOOGLE_API_KEY:
        raise HTTPException(status_code=400, detail="Missing GOOGLE_API_KEY. Please set it in the environment.")

    prompt = (
        "You are a helpful assistant. Answer the question using ONLY the provided context. "
        "Cite sources inline using the format [filename#chunkId]. If unknown, say you don't know.\n\n"
        f"Question: {q}\n\n"
        "Context:\n" + "\n---\n".join(context_texts)
    )

    try:
        model = genai.GenerativeModel(config.GENERATION_MODEL)
        resp = model.generate_content(prompt)
        answer = resp.text.strip() if getattr(resp, "text", None) else ""
        if not answer:
            logger.error(
                "Empty response from model %s (prompt_length=%d)",
                config.GENERATION_MODEL,
                len(prompt),
            )
            raise HTTPException(status_code=502, detail="Model returned empty response.")
    except HTTPException:
        # Already a well-formed HTTP error; let it bubble after being logged at debug level
        logger.debug("HTTPException during generation", exc_info=True)
        raise
    except Exception as e:
        # Log the original error with stack trace for troubleshooting
        logger.exception("Generation failed with error: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail="Failed to generate an answer. Verify API key, model access, and network.",
        )

    source_pairs = [
        {"filename": str(r[0].get("filename")), "chunkId": int(r[0].get("chunkId", 0))}
        for r in context_items
    ]

    return {"answer": answer, "sources": source_pairs}
