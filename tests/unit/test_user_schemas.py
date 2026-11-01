"""
Юнит-тесты Pydantic-схем модуля users.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.users.schemas import (
    PrivacySettings,
    UserChangePassword,
    UserCreate,
    UserReadMe,
    UserUpdate,
)


# ==============================================================================
# 1. UserCreate
# ==============================================================================
class TestUserCreate:
    """Тесты схемы регистрации."""

    def test_valid_data(self, user_data: dict) -> None:
        """Валидные данные → объект создаётся без ошибок."""

        user = UserCreate(**user_data)
        assert user.email == 'test_user@example.com'
        assert user.username == 'test_user_ivan'
        assert user.gender == 'M'
        assert user.preference == 'F'

    def test_passwords_mismatch(self, user_data: dict) -> None:
        """Несовпадение паролей → ValidationError."""

        user_data['password_confirm'] = 'different_password'
        with pytest.raises(ValidationError, match='Пароли не совпадают'):
            UserCreate(**user_data)

    def test_invalid_email(self, user_data: dict) -> None:
        """Невалидный email → ValidationError."""

        user_data['email'] = 'не-email'
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_missing_required_field(self, user_data: dict) -> None:
        """Пропущенное обязательное поле → ValidationError."""

        del user_data['email']
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_invalid_gender(self, user_data: dict) -> None:
        """Невалидное значение gender → ValidationError."""

        user_data['gender'] = 'X'
        with pytest.raises(ValidationError):
            UserCreate(**user_data)

    def test_invalid_birth_date(self, user_data: dict) -> None:
        """Невалидная дата рождения → ValidationError."""

        user_data['birth_date'] = 'не-дата'
        with pytest.raises(ValidationError):
            UserCreate(**user_data)


# ==============================================================================
# 2. UserChangePassword
# ==============================================================================
class TestUserChangePassword:
    """Тесты схемы смены пароля."""

    def test_valid_data(self) -> None:
        """Валидные данные → объект создаётся."""

        data = UserChangePassword(
            old_password='old_pass123',
            new_password='new_pass456',
            new_password_confirm='new_pass456',
        )
        assert data.old_password == 'old_pass123'
        assert data.new_password == 'new_pass456'

    def test_new_passwords_mismatch(self) -> None:
        """Несовпадение новых паролей → ValidationError."""

        with pytest.raises(ValidationError, match='Новые пароли не совпадают'):
            UserChangePassword(
                old_password='old_pass123',
                new_password='new_pass456',
                new_password_confirm='different',
            )


# ==============================================================================
# 3. UserUpdate
# ==============================================================================
class TestUserUpdate:
    """Тесты схемы обновления профиля."""

    def test_all_fields_optional(self) -> None:
        """Все поля опциональны → пустой объект создаётся."""

        data = UserUpdate()
        assert data.email is None
        assert data.first_name is None
        assert data.username is None

    def test_partial_update(self) -> None:
        """Частичное обновление → только переданные поля заполнены."""

        data = UserUpdate(first_name='Пётр', city='Москва')
        assert data.first_name == 'Пётр'
        assert data.city == 'Москва'
        assert data.email is None

    def test_invalid_email_in_update(self) -> None:
        """Невалидный email при обновлении → ValidationError."""

        with pytest.raises(ValidationError):
            UserUpdate(email='не-email')

    def test_exclude_unset(self) -> None:
        """model_dump(exclude_unset=True) возвращает только переданные поля."""

        data = UserUpdate(bio='Привет')
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {'bio': 'Привет'}
        assert 'email' not in dumped


# ==============================================================================
# 4. UserReadMe (computed_field)
# ==============================================================================
class TestUserReadMe:
    """Тесты схемы полного профиля с вычисляемыми полями."""

    @pytest.fixture
    def base_user_data(self) -> dict:
        """Базовые данные для UserReadMe."""

        return {
            'id': 1,
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Иван',
            'gender': 'M',
            'preference': 'F',
            'party_status': 'ready',
            'privacy_settings': PrivacySettings().model_dump(),
            'created_at': '2025-01-01T00:00:00+00:00',
        }

    def test_age_calculation(self, base_user_data: dict) -> None:
        """Возраст считается правильно."""

        # Ставим дату рождения — ровно 30 лет назад
        today = date.today()
        birth = date(today.year - 30, today.month, today.day)
        base_user_data['birth_date'] = birth.isoformat()

        user = UserReadMe(**base_user_data)
        assert user.age == 30

    def test_age_before_birthday(self, base_user_data: dict) -> None:
        """Если день рождения ещё не наступил в этом году → возраст на 1 меньше."""

        today = date.today()
        # День рождения через месяц
        birth_month = today.month + 1 if today.month < 12 else 1
        birth_year = today.year - 25
        birth = date(birth_year, birth_month, 1)
        base_user_data['birth_date'] = birth.isoformat()

        user = UserReadMe(**base_user_data)
        assert user.age == 24  # ещё не исполнилось 25

    def test_age_none_when_no_birth_date(self, base_user_data: dict) -> None:
        """Нет даты рождения → age = None."""

        base_user_data['birth_date'] = None
        user = UserReadMe(**base_user_data)
        assert user.age is None

    def test_is_adult_true(self, base_user_data: dict) -> None:
        """Возраст >= 18 → is_adult = True."""

        today = date.today()
        birth = date(today.year - 20, today.month, today.day)
        base_user_data['birth_date'] = birth.isoformat()

        user = UserReadMe(**base_user_data)
        assert user.is_adult is True

    def test_is_adult_false(self, base_user_data: dict) -> None:
        """Возраст < 18 → is_adult = False."""

        today = date.today()
        birth = date(today.year - 16, today.month, today.day)
        base_user_data['birth_date'] = birth.isoformat()

        user = UserReadMe(**base_user_data)
        assert user.is_adult is False

    def test_is_adult_none_birth_date(self, base_user_data: dict) -> None:
        """Нет даты рождения → is_adult = False."""

        base_user_data['birth_date'] = None
        user = UserReadMe(**base_user_data)
        assert user.is_adult is False

    def test_computed_fields_in_dump(self, base_user_data: dict) -> None:
        """Computed поля попадают в model_dump()."""

        today = date.today()
        birth = date(today.year - 25, today.month, today.day)
        base_user_data['birth_date'] = birth.isoformat()

        user = UserReadMe(**base_user_data)
        dumped = user.model_dump()
        assert 'age' in dumped
        assert 'is_adult' in dumped
        assert dumped['age'] == 25
        assert dumped['is_adult'] is True


# ==============================================================================
# 5. PrivacySettings
# ==============================================================================
class TestPrivacySettings:
    """Тесты настроек приватности."""

    def test_default_values(self) -> None:
        """Дефолтные значения совпадают с ожидаемыми."""

        ps = PrivacySettings()
        assert ps.show_first_name is True
        assert ps.show_last_name is True
        assert ps.show_birth_year is True
        assert ps.show_preference is True
        assert ps.show_city is True
        assert ps.show_bio is True
        assert ps.show_phone is False
        assert ps.show_vk is True
        assert ps.show_parties is True
        assert ps.show_friends is True

    def test_custom_values(self) -> None:
        """Можно переопределить любое поле."""

        ps = PrivacySettings(show_phone=True, show_bio=False)
        assert ps.show_phone is True
        assert ps.show_bio is False
        assert ps.show_first_name is True

    def test_model_dump(self) -> None:
        """model_dump() возвращает dict для сохранения в JSONB."""

        ps = PrivacySettings()
        dumped = ps.model_dump()
        assert isinstance(dumped, dict)
        assert 'show_phone' in dumped
        assert 'show_first_name' in dumped
