"""005_add_chunk_metadata_fields

Revision ID: a6a8f2534b26
Revises: de3cb0d71f8f
Create Date: 2026-07-27 07:12:30.424867+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = 'a6a8f2534b26'
down_revision: Union[str, None] = 'de3cb0d71f8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('document_chunks', sa.Column('page_number', sa.Integer(), nullable=True, comment='The page number this chunk originated from (1-indexed).'))
    op.add_column('document_chunks', sa.Column('language', sa.String(length=10), nullable=True, comment='Detected language for this specific chunk.'))


def downgrade() -> None:
    op.drop_column('document_chunks', 'language')
    op.drop_column('document_chunks', 'page_number')
