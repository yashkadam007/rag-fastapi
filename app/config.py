from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv


# Load environment variables from .env if present
load_dotenv()

# Base paths
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Files
VEC_PATH: Final[Path] = DATA_DIR / "vec.json"
REGISTRY_PATH: Final[Path] = DATA_DIR / "registry.json"

# Runtime configuration
GOOGLE_API_KEY: Final[str | None] = os.getenv("GOOGLE_API_KEY")
DEFAULT_WORKSPACE: Final[str] = os.getenv("DEFAULT_WORKSPACE", "default")
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")

try:
    MAX_UPLOAD_MB: Final[int] = int(os.getenv("MAX_UPLOAD_MB", "25"))
except ValueError:
    MAX_UPLOAD_MB = 25

MAX_UPLOAD_BYTES: Final[int] = MAX_UPLOAD_MB * 1024 * 1024

# Models
EMBEDDING_MODEL: Final[str] = "models/text-embedding-004"
# Use a stable alias by default; can be overridden via env
GENERATION_MODEL: Final[str] = os.getenv("GENERATION_MODEL", "gemini-2.5-flash")

# Database configuration (Neon Postgres)
DATABASE_URL: Final[str | None] = os.getenv("DATABASE_URL")
try:
    DB_POOL_SIZE: Final[int] = int(os.getenv("DB_POOL_SIZE", "5"))
except ValueError:
    DB_POOL_SIZE = 5
try:
    DB_MAX_OVERFLOW: Final[int] = int(os.getenv("DB_MAX_OVERFLOW", "5"))
except ValueError:
    DB_MAX_OVERFLOW = 5
try:
    DB_POOL_RECYCLE: Final[int] = int(os.getenv("DB_POOL_RECYCLE", "300"))
except ValueError:
    DB_POOL_RECYCLE = 300

# Feature flag for safe rollback to JSON registry
USE_JSON_REGISTRY: Final[bool] = os.getenv("USE_JSON_REGISTRY", "false").lower() == "true"

# Vector store configuration
try:
    EMBEDDING_DIM: Final[int] = int(os.getenv("EMBEDDING_DIM", "768"))
except ValueError:
    EMBEDDING_DIM = 768
USE_JSON_VECTOR_STORE: Final[bool] = os.getenv("USE_JSON_VECTOR_STORE", "false").lower() == "true"

# Auth/session configuration
SESSION_COOKIE_NAME: Final[str] = os.getenv("SESSION_COOKIE_NAME", "session")
SESSION_TOKEN_BYTES: Final[int] = int(os.getenv("SESSION_TOKEN_BYTES", "32"))
SESSION_TTL_SECONDS: Final[int] = int(os.getenv("SESSION_TTL_SECONDS", "1209600"))  # 14 days
PASSWORD_HASH_SCHEME: Final[str] = os.getenv("PASSWORD_HASH_SCHEME", "pbkdf2_sha256")

def data_file(path: Path) -> Path:
    """Ensure a data file exists; create with empty array if missing."""
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    return path


# Ensure store files exist
_ = data_file(VEC_PATH)
_ = data_file(REGISTRY_PATH)
