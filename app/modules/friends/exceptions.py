class FriendError(Exception):
    """Базовое исключение модуля дружеских связей."""

    message: str = 'Ошибка модуля друзей.'


class FriendRequestNotFoundError(FriendError):
    """Заявка в друзья не найдена."""

    message = 'Заявка в друзья не найдена.'


class FriendshipNotFoundError(FriendError):
    """Пользователи не являются друзьями."""

    message = 'Пользователи не являются друзьями.'


class SelfFriendshipError(FriendError):
    """Попытка добавить в друзья самого себя."""

    message = 'Нельзя добавить в друзья самого себя.'


class TargetUserNotFoundError(FriendError):
    """Пользователь, которого добавляют в друзья, не существует."""

    message = 'Пользователь не найден.'


class AlreadyFriendsError(FriendError):
    """Пользователи уже являются друзьями."""

    message = 'Вы уже состоите в друзьях.'


class FriendRequestAlreadySentError(FriendError):
    """Заявка уже отправлена (в любую из сторон)."""

    message = 'Заявка в друзья уже отправлена.'


class FriendRequestDeclinedError(FriendError):
    """Заявка была отклонена, повторная отправка запрещена."""

    message = 'Заявка уже была отклонена.'


class UserBlockedError(FriendError):
    """Текущий пользователь заблокирован целевым."""

    message = 'Пользователь недоступен для добавления в друзья.'


class UserBlockedByMeError(FriendError):
    """Целевой пользователь заблокирован текущим (сначала нужно разблокировать)."""

    message = 'Сначала разблокируйте пользователя.'


class BlockAlreadyExistsError(FriendError):
    """Пользователь уже заблокирован."""

    message = 'Пользователь уже заблокирован.'


class BlockNotFoundError(FriendError):
    """Записи о блокировке не существует."""

    message = 'Пользователь не заблокирован.'


class SelfBlockError(FriendError):
    """Попытка заблокировать самого себя."""

    message = 'Нельзя заблокировать самого себя.'
