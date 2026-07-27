"""Add hybrid chunking metadata

Revision ID: 361eae9fd985
Revises: a6a8f2534b26
Create Date: 2026-07-27 07:19:36.833064+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = '361eae9fd985'
down_revision: Union[str, None] = 'a6a8f2534b26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('document_chunks', sa.Column('chunking_strategy', sa.String(length=50), server_default='recursive', nullable=False, comment='The chunking strategy used to produce this chunk.'))
    op.add_column('document_chunks', sa.Column('section_title', sa.String(length=255), nullable=True, comment='Title of the section this chunk belongs to (if detected).'))
    op.add_column('document_chunks', sa.Column('section_level', sa.Integer(), nullable=True, comment='Heading depth level for the section (e.g., 1 for H1, 2 for H2).'))


def downgrade() -> None:
    op.drop_column('document_chunks', 'section_level')
    op.drop_column('document_chunks', 'section_title')
    op.drop_column('document_chunks', 'chunking_strategy')
