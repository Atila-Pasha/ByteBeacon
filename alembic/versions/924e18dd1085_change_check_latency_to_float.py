"""Change check latency to float

Revision ID: 924e18dd1085
Revises: f6ff6badecdf
Create Date: 2026-08-22 22:16:23.213709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '924e18dd1085'
down_revision: Union[str, Sequence[str], None] = 'f6ff6badecdf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('checks', 'latency',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('checks', 'latency',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)


