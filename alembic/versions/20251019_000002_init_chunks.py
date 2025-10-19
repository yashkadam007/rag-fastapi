from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "20251019_000002_init_chunks"
down_revision = "20251019_000001_init_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("file_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("workspace", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
    )
    op.create_index("idx_chunks_workspace", "chunks", ["workspace"], unique=False)
    op.create_index("idx_chunks_file_id", "chunks", ["file_id"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ivfflat_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_index("ivfflat_chunks_embedding", table_name="chunks")
    op.drop_index("idx_chunks_file_id", table_name="chunks")
    op.drop_index("idx_chunks_workspace", table_name="chunks")
    op.drop_table("chunks")


