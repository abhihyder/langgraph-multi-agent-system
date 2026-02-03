"""create feedbacks table

Revision ID: 004_feedbacks
Revises: 003_conversations
Create Date: 2026-01-27 15:10:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from database.migrations.helpers import (
    create_table,
    autoincrement_id,
    foreign_key,
    string,
    text,
    datetime,
    jsonb,
    create_indexes,
    drop_table_with_indexes
)

# revision identifiers, used by Alembic.
revision: str = '004_feedbacks'
down_revision: Union[str, None] = '003_conversations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Table name
table_name = 'feedbacks'


def upgrade() -> None:
    """Create feedbacks table."""
    create_table(
        table_name=table_name,
        columns=[
            autoincrement_id(),
            foreign_key('conversation_id', 'conversations'),
            string('action', length=20, nullable=False),
            text('reason'),
            text('edits'),
            jsonb('extra_data', default={}),
        ],
        constraints=[
            sa.CheckConstraint("action IN ('accept', 'reject', 'regenerate', 'edit')", name='check_feedback_action')
        ],
        include_timestamps=False
    )
    
    # Manually add created_at since we don't want updated_at
    op.add_column(table_name, datetime('created_at', nullable=False, server_default='CURRENT_TIMESTAMP'))
    
    create_indexes(table_name, [
        {'name': 'idx_feedback_action', 'columns': ['action']},
        {'name': 'idx_feedback_conversation', 'columns': ['conversation_id']}
    ])


def downgrade() -> None:
    """Drop feedbacks table."""
    drop_table_with_indexes(table_name, [
        'idx_feedback_conversation',
        'idx_feedback_action'
    ])
