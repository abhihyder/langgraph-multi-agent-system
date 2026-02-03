"""create personas table

Revision ID: 002_personas
Revises: 001_users
Create Date: 2026-01-27 15:10:01.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from database.migrations.helpers import (
    create_table,
    autoincrement_id,
    foreign_key,
    string,
    integer,
    datetime,
    jsonb,
    create_indexes,
    drop_table_with_indexes
)

# revision identifiers, used by Alembic.
revision: str = '002_personas'
down_revision: Union[str, None] = '001_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Table name
table_name = 'personas'


def upgrade() -> None:
    """Create personas table."""
    create_table(
        table_name=table_name,
        columns=[
            autoincrement_id(),
            foreign_key('user_id', 'users', use_integer=True),
            string('agent_type', length=100, nullable=False),
            string('tone', length=50, nullable=True, server_default='professional'),
            string('verbosity', length=50, nullable=True, server_default='balanced'),
            jsonb('style_preferences', default={}),
            integer('accepted_responses', server_default='0'),
            integer('rejected_responses', server_default='0'),
            jsonb('regeneration_patterns', default={}),
            jsonb('preferred_structures', default=[]),
            jsonb('domain_knowledge', default=[]),
            jsonb('learning_goals', default=[]),
            string('communication_style', length=100, nullable=True),
            datetime('last_used', nullable=True),
        ],
        constraints=[
            sa.UniqueConstraint('user_id', 'agent_type', name='uq_user_agent')
        ],
        include_timestamps=True
    )
    
    create_indexes(table_name, [
        {'name': 'idx_persona_user_agent', 'columns': ['user_id', 'agent_type']}
    ])


def downgrade() -> None:
    """Drop personas table."""
    drop_table_with_indexes(table_name, ['idx_persona_user_agent'])
