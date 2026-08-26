"""change time saving logic

Revision ID: 25db7b5bc9a4
Revises: c1410210c886
Create Date: 2026-08-21 13:42:45.830462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '25db7b5bc9a4'
down_revision: Union[str, Sequence[str], None] = 'c1410210c886'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
