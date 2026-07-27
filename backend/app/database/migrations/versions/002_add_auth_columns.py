"""002 add supabase user id and role to users

Revision ID: 002_auth
Revises: 001_initial
Create Date: 2026-07-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "002_auth"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add supabase_user_id column (temporarily nullable for migration)
    op.add_column(
        "users",
        sa.Column("supabase_user_id", sa.String(255), nullable=True),
    )
    # Add role column with server default
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="USER"),
    )

    # Backfill existing rows: set supabase_user_id to the string of id
    op.execute("UPDATE users SET supabase_user_id = id::text WHERE supabase_user_id IS NULL")

    # Now enforce NOT NULL
    op.alter_column("users", "supabase_user_id", nullable=False)

    # Create unique index
    op.create_index("ix_users_supabase_user_id", "users", ["supabase_user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_supabase_user_id", table_name="users")
    op.drop_column("users", "role")
    op.drop_column("users", "supabase_user_id")
