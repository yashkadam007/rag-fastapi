from __future__ import annotations

from sqlalchemy import BigInteger, Index, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from pgvector.sqlalchemy import Vector

from app import config


Base = declarative_base()


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    file_id: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    workspace: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(config.EMBEDDING_DIM), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)


Index("idx_chunks_workspace", Chunk.workspace)
Index("idx_chunks_file_id", Chunk.file_id)


