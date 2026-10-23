from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""


from app.modules.friends.models import Friendship
from app.modules.users.models import User

__all__ = [
    'Base',
    'Friendship',
    'User',
]
