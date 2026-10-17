class UserError(Exception):
    """Базовое исключение для модуля пользователей."""


class UserAuthError(UserError):
    """Ошибка аутентификации (неверный логин/пароль)."""


class UserInactiveError(UserError):
    """Пользователь деактивирован."""


class UserEmailAlreadyExistsError(UserError):
    """Пользователь с таким email уже существует."""


class UsernameAlreadyExistsError(UserError):
    """Пользователь с таким username уже существует."""
