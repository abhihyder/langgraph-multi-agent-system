"""create pgvector memory tables

Revision ID: 005_pgvector
Revises: 004_feedbacks
Create Date: 2026-02-10 12:00:00.000000

Creates tables for PGVector memory driver:
- memories: User conversation memories with vector embeddings
- global_knowledge: Company documentation/policies with vector embeddings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from database.migrations.helpers import (
    autoincrement_id,
    create_table,
    foreign_key,
    string,
    text,
    jsonb,
    datetime,
    array_text,
    array_float,
    create_indexes,
    drop_table_with_indexes
)

# revision identifiers, used by Alembic.
revision: str = '005_pgvector'
down_revision: Union[str, None] = '004_feedbacks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create pgvector extension and memory tables."""
    
    # Create pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Create memories table
    create_table(
        table_name='memories',
        columns=[
            autoincrement_id(),  # Auto-incrementing integer primary key
            foreign_key('user_id', 'users', use_integer=True, nullable=False),
            foreign_key('conversation_id', 'conversations', use_integer=True, nullable=True),
            text('content', nullable=False),
            array_text('tags', nullable=True, server_default='{}'),
            jsonb('metadata', default={}),
        ],
        include_timestamps=True
    )
    
    # Add vector column separately using raw SQL (pgvector extension required)
    op.execute("""
        ALTER TABLE memories 
        ADD COLUMN embedding vector(384);
    """)
    
    # Create indexes for memories table
    create_indexes('memories', [
        {'name': 'idx_memories_user_id', 'columns': ['user_id']},
        {'name': 'idx_memories_conversation_id', 'columns': ['conversation_id']}
    ])
    
    # Create GIN index for tags array
    op.execute("CREATE INDEX idx_memories_tags ON memories USING GIN(tags);")
    
    # Note: Vector index creation requires the table to have data first for IVFFlat
    # If needed, create manually after data insertion:
    # CREATE INDEX idx_memories_embedding ON memories USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
    
    # Create global_knowledge table
    create_table(
        table_name='global_knowledge',
        columns=[
            autoincrement_id(),  # Auto-incrementing integer primary key
            text('content', nullable=False),
            string('category', length=100, nullable=False),
            string('title', length=500, nullable=True),
            string('doc_id', length=255, nullable=True),
            array_text('tags', nullable=True, server_default='{}'),
            jsonb('metadata', default={}),
        ],
        include_timestamps=True
    )
    
    # Add vector column separately using raw SQL
    op.execute("""
        ALTER TABLE global_knowledge 
        ADD COLUMN embedding vector(384);
    """)
    
    # Create indexes for global_knowledge table
    create_indexes('global_knowledge', [
        {'name': 'idx_knowledge_category', 'columns': ['category']},
        {'name': 'idx_knowledge_doc_id', 'columns': ['doc_id'], 'unique': True}
    ])
    
    # Create GIN index for tags array
    op.execute("CREATE INDEX idx_knowledge_tags ON global_knowledge USING GIN(tags);")
    
    # Note: Vector index for global_knowledge (create manually after data):
    # CREATE INDEX idx_knowledge_embedding ON global_knowledge USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
    
    print("✅ PGVector tables created successfully!")
    print("⚠️  Note: Vector indexes (IVFFlat) should be created manually after inserting data")
    print("   For memories: CREATE INDEX idx_memories_embedding ON memories USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);")
    print("   For knowledge: CREATE INDEX idx_knowledge_embedding ON global_knowledge USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);")


def downgrade() -> None:
    """Drop pgvector tables and extension."""
    
    # Drop tables with their indexes
    drop_table_with_indexes('global_knowledge', [
        'idx_knowledge_tags',
        'idx_knowledge_doc_id',
        'idx_knowledge_category'
    ])
    
    drop_table_with_indexes('memories', [
        'idx_memories_tags',
        'idx_memories_conversation_id',
        'idx_memories_user_id'
    ])
    
    # Note: We don't drop the vector extension as other tables might use it
    # If you want to drop it, run manually: DROP EXTENSION IF EXISTS vector;
    
    print("✅ PGVector tables dropped successfully!")
