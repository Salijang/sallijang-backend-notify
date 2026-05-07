"""add_slack_enabled

Revision ID: c7d4a1e9f2b3
Revises: b5c9f3d2e1a8
Create Date: 2026-05-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'c7d4a1e9f2b3'
down_revision: Union[str, Sequence[str], None] = 'b5c9f3d2e1a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE notification_schema.notification_settings "
        "ADD COLUMN IF NOT EXISTS slack_enabled BOOLEAN NOT NULL DEFAULT TRUE"
    )


def downgrade() -> None:
    op.drop_column('notification_settings', 'slack_enabled', schema='notification_schema')
