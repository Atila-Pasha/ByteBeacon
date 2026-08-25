"""Add Telegram linking tables and chat linkage.

Revision ID: 3a4f7c7d9b11
Revises: b7c2d9e41a30
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "3a4f7c7d9b11"
down_revision: Union[str, Sequence[str], None] = "b7c2d9e41a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True))
    op.create_index(
        op.f("ix_users_telegram_chat_id"),
        "users",
        ["telegram_chat_id"],
        unique=True,
    )

    op.create_table(
        "telegram_connection_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telegram_connection_tokens_user_id"),
        "telegram_connection_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telegram_connection_tokens_token_hash"),
        "telegram_connection_tokens",
        ["token_hash"],
        unique=True,
    )

    op.add_column("notifications", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("notifications", sa.Column("provider", sa.String(length=50), nullable=False, server_default="telegram"))
    op.add_column("notifications", sa.Column("event_type", sa.String(length=20), nullable=False, server_default="down"))
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_notifications_user_id_users",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_notifications_incident_channel_event",
        "notifications",
        ["incident_id", "channel", "event_type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_notifications_incident_channel_event", "notifications", type_="unique")
    op.drop_constraint("fk_notifications_user_id_users", "notifications", type_="foreignkey")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_column("notifications", "user_id")
    op.drop_column("notifications", "provider")
    op.drop_column("notifications", "event_type")

    op.drop_index(op.f("ix_telegram_connection_tokens_token_hash"), table_name="telegram_connection_tokens")
    op.drop_index(op.f("ix_telegram_connection_tokens_user_id"), table_name="telegram_connection_tokens")
    op.drop_table("telegram_connection_tokens")

    op.drop_index(op.f("ix_users_telegram_chat_id"), table_name="users")
    op.drop_column("users", "telegram_chat_id")
