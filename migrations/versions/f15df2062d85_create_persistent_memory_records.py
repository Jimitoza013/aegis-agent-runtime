"""create persistent memory records

Revision ID: f15df2062d85
Revises:
Create Date: 2026-11-21 23:00:07.644670

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f15df2062d85"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # Enable pgvector before creating vector columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "memory_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("principal_id", sa.String(length=128), nullable=False),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_memory_records_expires_at",
        "memory_records",
        ["expires_at"],
        unique=False,
    )

    op.create_index(
        "ix_memory_records_tenant_principal",
        "memory_records",
        ["tenant_id", "principal_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_memory_records_tenant_principal",
        table_name="memory_records",
    )

    op.drop_index(
        "ix_memory_records_expires_at",
        table_name="memory_records",
    )

    op.drop_table("memory_records")
