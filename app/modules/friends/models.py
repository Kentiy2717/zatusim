from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.friends.enums import FriendshipStatus

if TYPE_CHECKING:
    from app.modules.users.models import User


class Friendship(Base):
    """Модель дружеской связи и заявок в друзья между пользователями."""

    __tablename__ = 'friendships'
    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='uq_friendship_user_friend'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    status: Mapped[FriendshipStatus] = mapped_column(
        Enum(FriendshipStatus, native_enum=False, length=20),
        default=FriendshipStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Связи ORM
    user: Mapped['User'] = relationship(
        'User', foreign_keys=[user_id], back_populates='sent_friendships'  # Отправленные заявки
    )
    friend: Mapped['User'] = relationship(
        'User', foreign_keys=[friend_id], back_populates='received_friendships'  # Входящие заявки
    )
