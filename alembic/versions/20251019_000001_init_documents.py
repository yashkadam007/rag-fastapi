from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251019_000001_init_documents"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("file_id", sa.String(), primary_key=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("workspace", sa.String(), nullable=False),
        sa.Column("num_chunks", sa.Integer(), nullable=False),
        sa.Column("indexed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
    )
    op.create_index("idx_documents_workspace", "documents", ["workspace"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_documents_workspace", table_name="documents")
    op.drop_table("documents")


