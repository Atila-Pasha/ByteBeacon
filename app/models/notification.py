from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
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