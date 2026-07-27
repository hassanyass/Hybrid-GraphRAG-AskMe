"""004_create_document_chunks

Revision ID: de3cb0d71f8f
Revises: 003_doc_file_size
Create Date: 2026-07-27 06:59:21.252830+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision: str = 'de3cb0d71f8f'
down_revision: Union[str, None] = '003_doc_file_size'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('document_chunks',
    sa.Column('id', sa.UUID(), nullable=False, comment='Unique chunk identifier.'),
    sa.Column('document_id', sa.UUID(), nullable=False, comment='Parent document reference.'),
    sa.Column('chunk_index', sa.Integer(), nullable=False, comment='Sequential position of this chunk within the document.'),
    sa.Column('content', sa.Text(), nullable=False, comment='The actual text content of the chunk.'),
    sa.Column('token_count', sa.Integer(), nullable=True, comment='Number of tokens in the chunk (model-dependent).'),
    sa.Column('embedding_id', sa.String(length=255), nullable=True, comment='Point ID of the vector in Qdrant.'),
    sa.Column('vector_status', sa.Enum('PENDING', 'EMBEDDED', 'INDEXED', 'FAILED', name='vector_status_enum', create_constraint=True), nullable=False, comment='Current status of vector embedding for this chunk.'),
    sa.Column('embedding_model', sa.String(length=100), nullable=True, comment='Name of the embedding model used (e.g. BGE-M3).'),
    sa.Column('entity_extraction_status', sa.Enum('PENDING', 'EXTRACTING', 'COMPLETED', 'FAILED', name='entity_extraction_status_enum', create_constraint=True), nullable=False, comment='Status of entity/relationship extraction from this chunk.'),
    sa.Column('graph_sync_status', sa.Enum('PENDING', 'SYNCED', 'FAILED', name='graph_sync_status_enum', create_constraint=True), nullable=False, comment='Status of synchronization to Neo4j knowledge graph.'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp of chunk creation.'),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp of last status update.'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_entity_extraction_status'), 'document_chunks', ['entity_extraction_status'], unique=False)
    op.create_index(op.f('ix_document_chunks_graph_sync_status'), 'document_chunks', ['graph_sync_status'], unique=False)
    op.create_index(op.f('ix_document_chunks_vector_status'), 'document_chunks', ['vector_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunks_vector_status'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_graph_sync_status'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_entity_extraction_status'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_document_id'), table_name='document_chunks')
    op.drop_table('document_chunks')
    # Drop the enum types created for this table
    sa.Enum(name='vector_status_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='entity_extraction_status_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='graph_sync_status_enum').drop(op.get_bind(), checkfirst=True)
