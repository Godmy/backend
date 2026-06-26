"""RAG infrastructure: pgvector extension + rag_project / rag_document / rag_chunk tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-25 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "rag_project",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedding_model", sa.String(255), nullable=False, server_default="nomic-embed-text"),
        sa.Column("embedding_dim", sa.Integer(), nullable=False, server_default="768"),
        sa.Column("chunk_size", sa.Integer(), nullable=False, server_default="512"),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False, server_default="64"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_rag_project_id", "rag_project", ["id"])
    op.create_index("ix_rag_project_name", "rag_project", ["name"])
    op.create_index("ix_rag_project_created_at", "rag_project", ["created_at"])

    op.create_table(
        "rag_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("rag_project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_document_id", "rag_document", ["id"])
    op.create_index("ix_rag_document_project_id", "rag_document", ["project_id"])
    op.create_index("ix_rag_document_status", "rag_document", ["status"])
    op.create_index("ix_rag_document_created_at", "rag_document", ["created_at"])

    op.create_table(
        "rag_chunk",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("rag_document.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("rag_project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_chunk_id", "rag_chunk", ["id"])
    op.create_index("ix_rag_chunk_document_id", "rag_chunk", ["document_id"])
    op.create_index("ix_rag_chunk_project_id", "rag_chunk", ["project_id"])
    op.create_index("ix_rag_chunk_created_at", "rag_chunk", ["created_at"])

    # Векторный столбец и HNSW-индекс через raw SQL
    op.execute("ALTER TABLE rag_chunk ADD COLUMN embedding vector(768)")
    op.execute(
        "CREATE INDEX ix_rag_chunk_embedding ON rag_chunk "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("rag_chunk")
    op.drop_table("rag_document")
    op.drop_table("rag_project")
    op.execute("DROP EXTENSION IF EXISTS vector")
