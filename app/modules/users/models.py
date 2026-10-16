import enum
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Gender(str, enum.Enum):
    MALE = 'M'
    FEMALE = 'F'


class Preference(str, enum.Enum):
    MALE = 'M'
    FEMALE = 'F'
    BOTH = 'B'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))

    gender: Mapped[Gender]
    preference: Mapped[Preference]

    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    def __repr__(self) -> str:
        return f'<User id={self.id} email={self.email}>'
