from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base



class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    interval: Mapped[int] = mapped_column(Integer, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="monitors")
    
    checks: Mapped[list["Check"]] = relationship(back_populates="monitor", cascade="all, delete-orphan")
    
    incidents: Mapped[list["Incident"]] = relationship(back_populates="monitor", cascade="all, delete-orphan")