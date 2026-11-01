from app.db.base_class import Base
from app.modules.friends.models import Friendship
from app.modules.users.models import User

__all__ = [
    'Base',
    'Friendship',
    'User',
]
