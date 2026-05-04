"""add_slack_webhook_url

Revision ID: b5c9f3d2e1a8
Revises: a4f8e2b1c9d0
Create Date: 2026-05-04 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b5c9f3d2e1a8'
down_revision: Union[str, Sequence[str], None] = 'a4f8e2b1c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'notification_settings',
        sa.Column('slack_webhook_url', sa.String(), nullable=True),
        schema='notification_schema'
    )


def downgrade() -> None:
    op.drop_column('notification_settings', 'slack_webhook_url', schema='notification_schema')
