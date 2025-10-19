from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column


Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    file_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    workspace: Mapped[str] = mapped_column(String, nullable=False)
    num_chunks: Mapped[int] = mapped_column(Integer, nullable=False)
    indexed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)


Index("idx_documents_workspace", Document.workspace)


