"""initial_schema

Revision ID: 3882df5a0a97
Revises:
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '3882df5a0a97'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('order_number', sa.String(), nullable=True),
        sa.Column('store_name', sa.String(), nullable=True),
        sa.Column('product_names', sa.String(), nullable=True),
        sa.Column('pickup_expected_at', sa.String(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='notification_schema',
    )
    op.create_index('ix_notification_schema_notifications_id', 'notifications', ['id'], unique=False, schema='notification_schema')
    op.create_index('ix_notification_schema_notifications_user_id', 'notifications', ['user_id'], unique=False, schema='notification_schema')
    op.create_index('ix_notification_schema_notifications_order_id', 'notifications', ['order_id'], unique=False, schema='notification_schema')


def downgrade() -> None:
    op.drop_index('ix_notification_schema_notifications_order_id', table_name='notifications', schema='notification_schema')
    op.drop_index('ix_notification_schema_notifications_user_id', table_name='notifications', schema='notification_schema')
    op.drop_index('ix_notification_schema_notifications_id', table_name='notifications', schema='notification_schema')
    op.drop_table('notifications', schema='notification_schema')
