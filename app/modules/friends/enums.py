from enum import StrEnum


class FriendshipStatus(StrEnum):
    """Перечисление статусов дружеской связи между пользователями."""

    PENDING = 'pending'  # Заявка отправлена, ожидает ответа
    ACCEPTED = 'accepted'  # Заявка принята, пользователи в друзья
    DECLINED = 'declined'  # Заявка отклонена получателем
    BLOCKED = 'blocked'  # Пользователь заблокирован (в чёрном списке)
