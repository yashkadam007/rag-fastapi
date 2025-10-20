from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Index, Integer, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
import uuid
from pgvector.sqlalchemy import Vector
from app import config

Base = declarative_base()



class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth0_sub: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    uploader_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String, nullable=True)
    num_chunks: Mapped[int] = mapped_column(Integer, nullable=False)
    indexed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)


Index("idx_documents_chat_id", Document.chat_id)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

Index("idx_messages_chat_id", Message.chat_id)
Index("idx_messages_chat_time", Message.chat_id, Message.created_at)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(config.EMBEDDING_DIM), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)


Index("idx_chunks_document_id", Chunk.document_id)

