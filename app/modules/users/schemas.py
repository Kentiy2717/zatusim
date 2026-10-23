from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, EmailStr, computed_field, model_validator

from app.core.schemas import AppBaseModel
from app.modules.users.enums import Gender, PartyStatus, Preference


class PrivacySettings(BaseModel):
    """Схема и дефолтные значения настроек приватности пользователя."""

    show_first_name: bool = True
    show_last_name: bool = True
    show_birth_year: bool = True
    show_preference: bool = True
    show_city: bool = True
    show_bio: bool = True
    show_phone: bool = False
    show_vk: bool = True
    show_parties: bool = True
    show_friends: bool = True


# ==============================================================================
# 1. РЕГИСТРАЦИЯ И СМЕНА ПАРОЛЯ
# ==============================================================================
class UserCreate(BaseModel):
    """Схема быстрой регистрации пользователя."""

    email: EmailStr
    password: str
    password_confirm: str
    username: str
    first_name: str
    birth_date: date
    gender: Gender
    preference: Preference

    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        """Проверка совпадения паролей при регистрации."""

        if self.password != self.password_confirm:
            raise ValueError('Пароли не совпадают')
        return self


class UserChangePassword(BaseModel):
    """Схема отдельной процедуры смены пароля."""

    old_password: str
    new_password: str
    new_password_confirm: str

    @model_validator(mode='after')
    def check_new_passwords_match(self) -> Self:
        """Проверка совпадения новых паролей."""

        if self.new_password != self.new_password_confirm:
            raise ValueError('Новые пароли не совпадают')
        return self


# ==============================================================================
# 2. РЕДАКТИРОВАНИЕ ПРОФИЛЯ
# ==============================================================================
class UserUpdate(BaseModel):
    """Схема обновления данных профиля (все поля опциональны)."""

    email: EmailStr | None = None
    avatar_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    gender: Gender | None = None
    preference: Preference | None = None
    birth_date: date | None = None
    bio: str | None = None
    city: str | None = None
    phone: str | None = None
    vk_link: str | None = None
    party_status: PartyStatus | None = None
    privacy_settings: PrivacySettings | None = None


# ==============================================================================
# 3. МИНИ-КАРТОЧКА (Списки, друзья, участники тусовки, лобби игр)
# ==============================================================================
class UserShort(AppBaseModel):
    """Легкая схема карточки пользователя."""

    id: int
    username: str
    first_name: str
    last_name: str | None = None
    avatar_url: str | None = None


# ==============================================================================
# 4. МОЙ ПРОФИЛЬ (Полная отдача данных для самого себя)
# ==============================================================================
class UserReadMe(AppBaseModel):
    """Полные данные собственного профиля."""

    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str | None = None
    gender: Gender
    preference: Preference
    avatar_url: str | None = None
    bio: str | None = None
    birth_date: date | None = None
    city: str | None = None
    phone: str | None = None
    vk_link: str | None = None
    party_status: PartyStatus
    privacy_settings: PrivacySettings
    created_at: datetime

    @computed_field
    def age(self) -> int | None:
        """Точный возраст на лету."""

        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @computed_field
    def is_adult(self) -> bool:
        """Флаг совершеннолетия (18+)."""

        user_age = self.age
        return user_age is not None and user_age >= 18


# ==============================================================================
# 5. ПУБЛИЧНЫЙ ПРОФИЛЬ (Чужая страница пользователя)
# ==============================================================================
class UserReadPublic(AppBaseModel):
    """Данные чужого профиля (фильтруются бизнес-логикой)."""

    id: int
    username: str
    first_name: str
    last_name: str | None = None
    gender: Gender | None = None
    preference: Preference | None = None
    avatar_url: str | None = None
    bio: str | None = None
    birth_date: date | None = None
    city: str | None = None
    phone: str | None = None
    vk_link: str | None = None
    party_status: PartyStatus

    @computed_field
    def age(self) -> int | None:
        """Вычисление возраста (если дата рождения не скрыта приватностью)."""
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @computed_field
    def is_adult(self) -> bool:
        """Флаг совершеннолетия (18+)."""
        user_age = self.age
        return user_age is not None and user_age >= 18
