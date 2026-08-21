from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, false, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        server_default="open",
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    monitor: Mapped["Monitor"] = relationship(
        back_populates="incidents",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )