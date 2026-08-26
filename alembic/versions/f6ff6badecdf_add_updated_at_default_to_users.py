"""add updated_at default to users

Revision ID: f6ff6badecdf
Revises: 64447df127f7
Create Date: 2026-08-21 15:50:01.477473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6ff6badecdf'
down_revision: Union[str, Sequence[str], None] = '64447df127f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=sa.text("now()"),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=None,
    )
