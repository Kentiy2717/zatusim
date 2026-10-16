from pydantic import BaseModel, EmailStr

from app.core.schemas import AppBaseModel
from app.modules.users.models import Gender, Preference


class UserBase(BaseModel):
    """Базовые атрибуты пользователя."""

    email: EmailStr
    first_name: str
    last_name: str | None = None
    gender: Gender
    preference: Preference


class UserCreate(UserBase):
    """Схема входных данных для регистрации пользователя."""

    password: str


class UserRead(UserBase, AppBaseModel):
    """Схема публичных данных пользователя в API-ответах."""

    id: int
