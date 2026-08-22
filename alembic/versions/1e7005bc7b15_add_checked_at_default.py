"""Add checked_at default

Revision ID: 1e7005bc7b15
Revises: 924e18dd1085
Create Date: 2026-08-22 22:52:40.444896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e7005bc7b15'
down_revision: Union[str, Sequence[str], None] = '924e18dd1085'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "checks",
        "checked_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "checks",
        "checked_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
