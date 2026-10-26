"""ORM-модели: пользователи и их OAuth-токены."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Текущее время в UTC (осознанное, не naive)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Базовый класс всех ORM-моделей."""


class User(Base):
    """Пользователь, вошедший через внешнего провайдера (Google/YouTube)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), default="google")
    # "sub" из ID-токена — стабильный идентификатор пользователя у провайдера.
    subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    tokens: Mapped[list["OAuthToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_users_provider_subject"),
    )


class OAuthToken(Base):
    """OAuth-токены пользователя. Значения access/refresh хранятся зашифрованными."""

    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(32), default="google")
    access_token: Mapped[str] = mapped_column(Text)  # шифротекст
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # шифротекст
    token_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped[User] = relationship(back_populates="tokens")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_tokens_user_provider"),
    )
