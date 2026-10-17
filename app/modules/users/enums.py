from enum import StrEnum


class Gender(StrEnum):
    """Пол пользователя."""

    MALE = 'M'
    FEMALE = 'F'


class Preference(StrEnum):
    """Предпочтения пользователя."""

    MALE = 'M'
    FEMALE = 'F'
    BOTH = 'B'


class PartyStatus(StrEnum):
    """Статусы готовности пользователя к тусовкам."""

    READY = 'ready'  # Готов ворваться (Принимает инвайты от всех пользователей)
    BUSY = 'busy'  # Уже тусю (Можно кинуть инвайт, но только из знакомых тусовок)
    SNOOZE = 'snooze'  # Не беспокоить (Блокирует все инвайты и уведомления)
