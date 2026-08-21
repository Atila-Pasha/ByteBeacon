from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    latency: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    monitor: Mapped["Monitor"] = relationship(
        back_populates="checks",
    )