class UserAuthError(Exception):
    """Ошибка аутентификации (неверный логин или пароль)."""


class UserInactiveError(Exception):
    """Пользователь деактивирован."""
