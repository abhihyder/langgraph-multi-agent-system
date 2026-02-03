"""create users table

Revision ID: 001_users
Revises: 
Create Date: 2026-01-27 15:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from database.migrations.helpers import (
    create_table,
    autoincrement_id,
    string,
    boolean,
    datetime,
    create_indexes,
    drop_table_with_indexes
)

# revision identifiers, used by Alembic.
revision: str = '001_users'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Table name
table_name = 'users'


def upgrade() -> None:
    """Create users table."""
    create_table(
        table_name=table_name,
        columns=[
            autoincrement_id(),
            string('google_id', nullable=False),
            string('email', nullable=False),
            string('name', nullable=True),
            string('picture', length=500, nullable=True),
            boolean('is_active', server_default='true'),
            boolean('is_admin', server_default='false'),
            datetime('last_login', nullable=True),
        ],
        include_timestamps=True
    )
    
    create_indexes(table_name, [
        {'name': 'ix_users_email', 'columns': ['email'], 'unique': True},
        {'name': 'ix_users_google_id', 'columns': ['google_id'], 'unique': True}
    ])


def downgrade() -> None:
    """Drop users table."""
    drop_table_with_indexes(table_name, [
        'ix_users_google_id',
        'ix_users_email'
    ])
