from pydantic import BaseModel, ConfigDict

from app.modules.friends.enums import FriendshipStatus


class AppBaseModel(BaseModel):
    """Базовая Pydantic-схема проекта с поддержкой чтения ORM-атрибутов."""

    model_config = ConfigDict(from_attributes=True)


class RelationBrief(BaseModel):
    """Краткое состояние связи между текущим пользователем и кем-то ещё.

    Живёт в ``core``, а не в модуле ``friends``, чтобы карточки пользователей
    (поиск, участники тусовок) могли его переиспользовать без циклических
    импортов между модулями.
    """

    status: FriendshipStatus | None = None
    friendship_id: int | None = None
    is_friend: bool = False
    is_incoming_request: bool = False
    is_outgoing_request: bool = False
    is_declined: bool = False
    is_blocked_by_me: bool = False
    is_blocked_me: bool = False
