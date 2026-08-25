from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "incident_id",
            "channel",
            "event_type",
            name="uq_notifications_incident_channel_event",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="telegram",
        server_default="telegram",
    )

    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="down",
        server_default="down",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="notifications",
    )

    user: Mapped["User"] = relationship(
        back_populates="notifications",
    )