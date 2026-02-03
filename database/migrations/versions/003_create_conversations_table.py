"""create conversations table

Revision ID: 003_conversations
Revises: 002_personas
Create Date: 2026-01-27 15:10:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from database.migrations.helpers import (
    create_table,
    autoincrement_id,
    foreign_key,
    text,
    integer,
    datetime,
    jsonb,
    create_indexes,
    drop_table_with_indexes
)

# revision identifiers, used by Alembic.
revision: str = '003_conversations'
down_revision: Union[str, None] = '002_personas'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Table name
table_name = 'conversations'


def upgrade() -> None:
    """Create conversations table."""
    create_table(
        table_name=table_name,
        columns=[
            autoincrement_id(),
            foreign_key('user_id', 'users', use_integer=True),
            text('query', nullable=False),
            text('response', nullable=False),
            jsonb('agents_used', default=[]),
            jsonb('conversation_metadata', default={}),
        ],
        include_timestamps=False
    )
    
    # Manually add created_at since we don't want updated_at
    op.add_column(table_name, datetime('created_at', nullable=False, server_default='CURRENT_TIMESTAMP'))
    
    create_indexes(table_name, [
        {'name': 'idx_conversation_user_date', 'columns': ['user_id', 'created_at']},
        {'name': 'ix_conversations_created_at', 'columns': ['created_at']}
    ])


def downgrade() -> None:
    """Drop conversations table."""
    drop_table_with_indexes(table_name, [
        'ix_conversations_created_at',
        'idx_conversation_user_date'
    ])
