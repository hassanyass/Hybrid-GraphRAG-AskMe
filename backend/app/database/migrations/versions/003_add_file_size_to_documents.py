"""003 add file size to documents

Revision ID: 003_doc_file_size
Revises: 002_auth
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_doc_file_size'
down_revision: Union[str, None] = '002_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add file_size column (temporarily nullable)
    op.add_column('documents', sa.Column('file_size', sa.Integer(), nullable=True))
    
    # Backfill existing rows with 0
    op.execute('UPDATE documents SET file_size = 0 WHERE file_size IS NULL')
    
    # Enforce NOT NULL
    op.alter_column('documents', 'file_size', nullable=False)


def downgrade() -> None:
    op.drop_column('documents', 'file_size')
