"""Add a server default for incident start timestamps.

Revision ID: b7c2d9e41a30
Revises: 1e7005bc7b15
Create Date: 2026-08-25 17:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b7c2d9e41a30"
down_revision: Union[str, Sequence[str], None] = "1e7005bc7b15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "incidents",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "incidents",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
