from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.modules.friends.enums import FriendshipStatus

if TYPE_CHECKING:
    from app.modules.users.models import User


class Friendship(Base):
    """Дружеская связь между двумя пользователями.

    Хранится одна строка на пару пользователей в каноническом виде:
    ``user_id`` всегда меньше ``friend_id``, а автор заявки указывается
    в ``initiator_id``. Это исключает дубли «A→B» и «B→A» на уровне БД
    и позволяет искать связь одним запросом по составному индексу.

    Отклонённая заявка сохраняется со статусом ``DECLINED`` (а не удаляется),
    чтобы заблокировать повторную отправку той же пары.
    """

    __tablename__ = 'friendships'
    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='uq_friendship_pair'),
        CheckConstraint('user_id < friend_id', name='ck_friendship_canonical_pair'),
        # Составной индекс под выборку «все связи пользователя в нужном статусе»
        Index(
            'ix_friendships_status_user',
            'status',
            'user_id',
            'friend_id',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Каноническая пара: id меньшего пользователя + id большего
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    friend_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True
    )

    # Кто именно отправил заявку (совпадает с user_id или friend_id)
    initiator_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))

    status: Mapped[FriendshipStatus] = mapped_column(
        SQLEnum(FriendshipStatus, native_enum=False, length=20),
        default=FriendshipStatus.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ORM-связи
    user: Mapped['User'] = relationship(
        'User', foreign_keys=[user_id], back_populates='friendships_low'
    )
    friend: Mapped['User'] = relationship(
        'User', foreign_keys=[friend_id], back_populates='friendships_high'
    )
    initiator: Mapped['User'] = relationship('User', foreign_keys=[initiator_id])

    def __repr__(self) -> str:
        return (
            f'<Friendship pair=({self.user_id}, {self.friend_id}) '
            f'status={self.status}>'
        )

    # ------------------------------------------------------------------
    # Вспомогательные методы канонической пары
    # ------------------------------------------------------------------
    def partner_id(self, user_id: int) -> int:
        """Возвращает id второго участника пары относительно переданного.

        Имя намеренно не совпадает с полем ``other_user`` схем ответа:
        Pydantic при ``from_attributes=True`` подхватил бы метод вместо
        вычисляемого значения.
        """

        return self.friend_id if self.user_id == user_id else self.user_id

    def partner(self, user_id: int) -> 'User':
        """Возвращает объект второго участника пары (требует загруженных связей)."""

        return self.friend if self.user_id == user_id else self.user

    def is_pending_for(self, user_id: int) -> bool:
        """True, если заявка ожидает ответа именно от этого пользователя."""

        return (
            self.status == FriendshipStatus.PENDING
            and self.initiator_id != user_id
        )


class Block(Base):
    """Запись о блокировке: ``blocker_id`` заблокировал ``blocked_id``.

    Направленная связь, хранится отдельно от ``Friendship``, чтобы блокировка
    не занимала слот дружбы и не требовала удаления истории заявок.
    """

    __tablename__ = 'blocks'
    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='uq_block_pair'),
        CheckConstraint('blocker_id <> blocked_id', name='ck_block_not_self'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    blocker_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    blocked_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    blocker: Mapped['User'] = relationship(
        'User', foreign_keys=[blocker_id], back_populates='blocks_made'
    )
    blocked: Mapped['User'] = relationship(
        'User', foreign_keys=[blocked_id], back_populates='blocks_received'
    )

    def __repr__(self) -> str:
        return f'<Block {self.blocker_id} -> {self.blocked_id}>'
