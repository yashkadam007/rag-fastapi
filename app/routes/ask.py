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

