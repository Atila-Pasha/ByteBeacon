from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    
    firstname: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    lastname: Mapped[str] = mapped_column(
        String(150),
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    monitors: Mapped[list["Monitor"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )