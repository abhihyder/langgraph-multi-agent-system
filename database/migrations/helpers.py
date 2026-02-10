"""
Migration helper utilities for reusable patterns.

Provides common functions to reduce boilerplate in migration files.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import List, Optional, Dict, Any


def autoincrement_id(name: str = 'id', bigint: bool = False):
    """
    Create an auto-incrementing integer ID column.
    
    Args:
        name: Column name (default: 'id')
        bigint: Use BIGINT instead of INTEGER for larger range
    """
    column_type = sa.BigInteger() if bigint else sa.Integer()
    return sa.Column(name, column_type, primary_key=True, autoincrement=True, nullable=False)

def uuid(name: str = 'uuid', primary_key: bool = False, nullable: bool = False):
    """Create a UUID column (commonly used for unique identifiers)."""
    return sa.Column(name, sa.UUID(), nullable=nullable, primary_key=primary_key)



def string(name: str, length: int = 255, nullable: bool = True, unique: bool = False, server_default: Optional[str] = None):
    """Create a VARCHAR/String column."""
    return sa.Column(name, sa.String(length=length), nullable=nullable, unique=unique, server_default=server_default)


def text(name: str, nullable: bool = True, server_default: Optional[str] = None):
    """Create a TEXT column for long-form content."""
    return sa.Column(name, sa.Text(), nullable=nullable, server_default=server_default)


def boolean(name: str, nullable: bool = False, server_default: Optional[str] = None):
    """Create a BOOLEAN column."""
    return sa.Column(name, sa.Boolean(), nullable=nullable, server_default=server_default)


def integer(name: str, nullable: bool = True, server_default: Optional[str] = None):
    """Create an INTEGER column."""
    return sa.Column(name, sa.Integer(), nullable=nullable, server_default=server_default)


def bigint(name: str, nullable: bool = True, server_default: Optional[str] = None):
    """Create a BIGINT column for large integers."""
    return sa.Column(name, sa.BigInteger(), nullable=nullable, server_default=server_default)


def float(name: str, nullable: bool = True, server_default: Optional[str] = None):
    """Create a FLOAT column for floating-point numbers."""
    return sa.Column(name, sa.Float(), nullable=nullable, server_default=server_default)


def decimal(name: str, precision: int = 10, scale: int = 2, nullable: bool = True, server_default: Optional[str] = None):
    """Create a DECIMAL/NUMERIC column for precise decimal numbers."""
    return sa.Column(name, sa.Numeric(precision=precision, scale=scale), nullable=nullable, server_default=server_default)


def datetime(name: str, nullable: bool = True, server_default: Optional[str] = None):
    """Create a DATETIME column."""
    return sa.Column(name, sa.DateTime(), nullable=nullable, server_default=sa.text(server_default) if server_default else None)


def foreign_key(
    name: str, 
    references_table: str, 
    references_column: str = 'id',
    on_delete: str = 'CASCADE',
    use_integer: bool = True, 
    bigint: bool = False, 
    nullable: bool = False
):
    """
    Create a foreign key column with reference.
    
    Args:
        name: Column name
        references_table: Table this column references
        references_column: Column in the referenced table (default: 'id')
        on_delete: ON DELETE action (default: 'CASCADE')
        use_integer: Use INTEGER/BIGINT instead of UUID
        bigint: Use BIGINT instead of INTEGER (only if use_integer=True)
        nullable: Whether the column can be NULL
    """
    column_type: Any
    if use_integer:
        column_type = sa.BigInteger() if bigint else sa.Integer()
    else:
        column_type = sa.UUID()
    
    return sa.Column(
        name, 
        column_type, 
        sa.ForeignKey(f'{references_table}.{references_column}', ondelete=on_delete),
        nullable=nullable
    )


def timestamps():
    """Create standard timestamp columns (created_at, updated_at)."""
    return [
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, 
                 server_default=sa.text('CURRENT_TIMESTAMP'),
                 onupdate=sa.text('CURRENT_TIMESTAMP'))
    ]


def jsonb(name: str, default: Any = None):
    """Create a JSONB column with optional default."""
    if default is None:
        server_default = None
    elif isinstance(default, dict):
        server_default = '{}'
    elif isinstance(default, list):
        server_default = '[]'
    else:
        server_default = str(default)
    
    return sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), 
                    nullable=True, server_default=server_default)


def array_text(name: str, nullable: bool = True, server_default: str = '{}'):
    """
    Create a PostgreSQL ARRAY(TEXT) column.
    
    Args:
        name: Column name
        nullable: Whether the column can be NULL
        server_default: Default value (default: '{}' for empty array)
    """
    return sa.Column(name, postgresql.ARRAY(sa.Text()), nullable=nullable, server_default=server_default)


def array_float(name: str, nullable: bool = True, server_default: Optional[str] = None):
    """
    Create a PostgreSQL ARRAY(FLOAT) column for vector embeddings.
    
    Args:
        name: Column name (commonly 'embedding')
        nullable: Whether the column can be NULL
        server_default: Default value (default: None)
    """
    return sa.Column(name, postgresql.ARRAY(sa.Float()), nullable=nullable, server_default=server_default)


def add_foreign_key(
    table_name: str,
    column_name: str,
    referenced_table: str,
    referenced_column: str = 'id',
    on_delete: str = 'CASCADE'
):
    """Add a foreign key constraint."""
    return sa.ForeignKeyConstraint(
        [column_name], 
        [f'{referenced_table}.{referenced_column}'], 
        ondelete=on_delete
    )


def create_table(
    table_name: str,
    columns: List,
    foreign_keys: Optional[List] = None,
    constraints: Optional[List] = None,
    include_timestamps: bool = True,
):
    """
    Create a table with standard patterns.
    
    Args:
        table_name: Name of the table
        columns: List of additional columns beyond id and timestamps
        foreign_keys: List of foreign key constraints
        constraints: List of additional constraints
        include_timestamps: Whether to add created_at/updated_at columns
    """

    all_columns: List[Any] = columns
    
    if include_timestamps:
        all_columns.extend(timestamps())
    
    table_args: List[Any] = []
    if foreign_keys:
        table_args.extend(foreign_keys)
    if constraints:
        table_args.extend(constraints)
        
    op.create_table(table_name, *all_columns, *table_args)


def create_indexes(table_name: str, indexes: List[Dict[str, Any]]):
    """
    Create multiple indexes for a table.
    
    Args:
        table_name: Name of the table
        indexes: List of dicts with keys: name, columns, unique (optional)
        
    Example:
        create_indexes('users', [
            {'name': 'idx_users_email', 'columns': ['email'], 'unique': True},
            {'name': 'idx_users_created', 'columns': ['created_at']}
        ])
    """
    for idx in indexes:
        name = idx['name']
        columns = idx['columns']
        unique = idx.get('unique', False)
        op.create_index(name, table_name, columns, unique=unique)


def drop_indexes(table_name: str, index_names: List[str]):
    """Drop multiple indexes from a table."""
    for name in index_names:
        op.drop_index(name, table_name=table_name)


def drop_table_with_indexes(table_name: str, indexes: List[str]):
    """Drop all indexes and then the table."""
    drop_indexes(table_name, indexes)
    op.drop_table(table_name)


# ============================================================
# ALTER TABLE HELPERS
# ============================================================

def add_column(table_name: str, column):
    """Add a column to an existing table."""
    op.add_column(table_name, column)


def add_columns(table_name: str, columns: List):
    """
    Add multiple columns to an existing table.
    
    Args:
        table_name: Name of the table
        columns: List of column definitions
        
    Example:
        add_columns('users', [
            string('phone', length=20),
            boolean('verified', server_default='false'),
            datetime('verified_at', nullable=True)
        ])
    """
    for column in columns:
        op.add_column(table_name, column)


def drop_column(table_name: str, column_name: str):
    """Drop a column from an existing table."""
    op.drop_column(table_name, column_name)


def drop_columns(table_name: str, column_names: List[str]):
    """
    Drop multiple columns from an existing table.
    
    Args:
        table_name: Name of the table
        column_names: List of column names to drop
        
    Example:
        drop_columns('users', ['phone', 'verified', 'verified_at'])
    """
    for column_name in column_names:
        op.drop_column(table_name, column_name)


def rename_column(table_name: str, old_name: str, new_name: str):
    """Rename a column in an existing table."""
    op.alter_column(table_name, old_name, new_column_name=new_name)


def modify_column(
    table_name: str,
    column_name: str,
    new_type=None,
    nullable: Optional[bool] = None,
    server_default=None
):
    """
    Modify a column in an existing table.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column to modify
        new_type: New column type (e.g., sa.String(100))
        nullable: Whether column should be nullable
        server_default: New server default value
    """
    op.alter_column(
        table_name,
        column_name,
        type_=new_type,
        nullable=nullable,
        server_default=server_default
    )


def add_constraint(table_name: str, constraint):
    """
    Add a constraint to an existing table.
    
    Example:
        add_constraint('users', sa.UniqueConstraint('email', name='uq_users_email'))
        add_constraint('products', sa.CheckConstraint('price > 0', name='check_positive_price'))
    """
    constraint_name = str(constraint.name) if constraint.name else None
    
    if isinstance(constraint, sa.UniqueConstraint):
        op.create_unique_constraint(constraint_name, table_name, list(constraint.columns.keys()))
    elif isinstance(constraint, sa.CheckConstraint):
        op.create_check_constraint(constraint_name, table_name, str(constraint.sqltext))
    elif isinstance(constraint, sa.ForeignKeyConstraint):
        op.create_foreign_key(
            constraint_name, 
            table_name, 
            str(constraint.referred_table.name) if hasattr(constraint, 'referred_table') else '',
            [str(col.name) for col in constraint.columns],
            [str(col.name) for col in constraint.elements]
        )
    else:
        raise ValueError(f"Unsupported constraint type: {type(constraint)}")


def drop_constraint(table_name: str, constraint_name: str, type_: str = 'foreignkey'):
    """
    Drop a constraint from an existing table.
    
    Args:
        table_name: Name of the table
        constraint_name: Name of the constraint to drop
        type_: Constraint type ('foreignkey', 'unique', 'check', 'primary')
    """
    op.drop_constraint(constraint_name, table_name, type_=type_)


def rename_table(old_name: str, new_name: str):
    """Rename an existing table."""
    op.rename_table(old_name, new_name)
