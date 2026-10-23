from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Date, DateTime, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.users.enums import Gender, PartyStatus, Preference
from app.modules.users.schemas import PrivacySettings

if TYPE_CHECKING:
    from app.modules.friends.models import Friendship


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # --- Личные данные профиля ---
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender, native_enum=False))
    preference: Mapped[Preference] = mapped_column(SQLEnum(Preference, native_enum=False))
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)

    city: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    vk_link: Mapped[str | None] = mapped_column(String(100))

    # Статус готовности к тусовкам
    party_status: Mapped[PartyStatus] = mapped_column(
        SQLEnum(PartyStatus, native_enum=False),
        default=PartyStatus.READY
    )

    # --- Настройки приватности ---
    privacy_settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: PrivacySettings().model_dump()
    )

    # Взаимосвязи с моделью Friendship
    sent_friendships: Mapped[list[Friendship]] = relationship(
        'Friendship', foreign_keys='Friendship.user_id', back_populates='user'
    )
    received_friendships: Mapped[list[Friendship]] = relationship(
        'Friendship', foreign_keys='Friendship.friend_id', back_populates='friend'
    )

    def __repr__(self) -> str:
        return f'<User id={self.id} username={self.username}>'
