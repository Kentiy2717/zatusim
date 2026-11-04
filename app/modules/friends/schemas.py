from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.core.schemas import AppBaseModel, RelationBrief
from app.modules.friends.enums import FriendshipStatus
from app.modules.users.schemas import UserShort


class FriendRequestCreate(BaseModel):
    """Запрос на добавление пользователя в друзья."""

    username: str | None = Field(
        default=None,
        max_length=30,
        description='Username пользователя, которому отправляется заявка',
    )
    user_id: int | None = Field(
        default=None,
        description='ID пользователя, которому отправляется заявка',
    )

    @model_validator(mode='after')
    def check_identifier_present(self) -> 'FriendRequestCreate':
        """Ровно один идентификатор должен быть передан."""

        if bool(self.username) == bool(self.user_id):
            raise ValueError(
                'Передайте ровно один идентификатор: username или user_id'
            )
        return self


class BlockCreate(BaseModel):
    """Запрос на блокировку пользователя."""

    username: str | None = Field(default=None, max_length=30)
    user_id: int | None = None

    @model_validator(mode='after')
    def check_identifier_present(self) -> 'BlockCreate':
        """Ровно один идентификатор должен быть передан."""

        if bool(self.username) == bool(self.user_id):
            raise ValueError(
                'Передайте ровно один идентификатор: username или user_id'
            )
        return self


class FriendshipRead(AppBaseModel):
    """Дружеская связь глазами конкретного пользователя.

    Поле ``other_user`` всегда содержит собеседника относительно того,
    кто выполняет запрос, поэтому клиенту не нужно знать о каноническом
    порядке хранения пары.
    """

    id: int
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime

    user: UserShort
    friend: UserShort
    initiator_id: int

    other_user: UserShort | None = None
    initiated_by_me: bool | None = None

    def with_perspective(self, current_user_id: int) -> 'FriendshipRead':
        """Заполняет поля «другой пользователь» и «я инициатор»."""

        is_low_side = self.user.id == current_user_id
        self.other_user = self.friend if is_low_side else self.user
        self.initiated_by_me = self.initiator_id == current_user_id
        return self


class FriendRequestRead(FriendshipRead):
    """Заявка в друзья (входящая или исходящая).

    Для входящей заявки автор — это ``other_user``, для исходящей — текущий
    пользователь, поэтому отдельное поле автора не требуется.
    """


class BlockRead(AppBaseModel):
    """Запись чёрного списка."""

    id: int
    blocked_id: int
    created_at: datetime

    blocked: UserShort


# Совместимость имён внутри модуля
UserRelationBrief = RelationBrief


class RelationRead(RelationBrief):
    """Текущее состояние связи «я и указанный пользователь»."""

    user_id: int
