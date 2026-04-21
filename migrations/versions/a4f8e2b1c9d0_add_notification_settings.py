"""add_notification_settings

Revision ID: a4f8e2b1c9d0
Revises: 3882df5a0a97
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a4f8e2b1c9d0'
down_revision: Union[str, Sequence[str], None] = '3882df5a0a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notification_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('new_order', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('review', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        schema='notification_schema',
    )
    op.create_index('ix_notification_schema_notification_settings_id', 'notification_settings', ['id'], unique=False, schema='notification_schema')
    op.create_index('ix_notification_schema_notification_settings_user_id', 'notification_settings', ['user_id'], unique=True, schema='notification_schema')


def downgrade() -> None:
    op.drop_index('ix_notification_schema_notification_settings_user_id', table_name='notification_settings', schema='notification_schema')
    op.drop_index('ix_notification_schema_notification_settings_id', table_name='notification_settings', schema='notification_schema')
    op.drop_table('notification_settings', schema='notification_schema')
