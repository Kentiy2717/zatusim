"""
Интеграционные тесты защищённых роутов (требуют авторизации).
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.modules.users.models import User


# ==============================================================================
# ФИКСТУРА: подмена авторизации
# ==============================================================================
@pytest.fixture
async def auth_client(
    client: AsyncClient,
    db: AsyncSession,
    user_data: dict,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Клиент с подменённой авторизацией.
    """

    from app.modules.users.schemas import UserCreate
    from app.modules.users.service import UserService

    user_create = UserCreate(**user_data)
    user = await UserService.create_user(session=db, user_in=user_create)

    # Подменяем зависимость: любой запрос будет "от имени" этого юзера
    async def fake_current_user() -> User:
        return user

    from app.main import app
    app.dependency_overrides[get_current_user] = fake_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# GET /me
# ==============================================================================
class TestGetMe:
    """Тесты GET /api/v1/users/me."""

    async def test_success(self, auth_client: AsyncClient, user_data: dict) -> None:
        """
        Авторизованный запрос → 200 + данные профиля.
        """

        response = await auth_client.get('/api/v1/users/me')

        assert response.status_code == 200
        data = response.json()
        assert data['email'] == user_data['email']
        assert data['first_name'] == user_data['first_name']
        assert 'age' in data
        assert 'is_adult' in data

    async def test_unauthorized(self, client: AsyncClient) -> None:
        """
        Без токена → 401.
        """

        # Используем обычный client (НЕ auth_client)
        response = await client.get('/api/v1/users/me')
        assert response.status_code == 401


# ==============================================================================
# PATCH /me
# ==============================================================================
class TestUpdateMe:
    """Тесты PATCH /api/v1/users/me."""

    async def test_update_first_name(
        self, auth_client: AsyncClient
    ) -> None:
        """Частичное обновление → только переданные поля меняются."""

        response = await auth_client.patch(
            '/api/v1/users/me',
            json={'first_name': 'Пётр'},
        )

        assert response.status_code == 200
        assert response.json()['first_name'] == 'Пётр'

    async def test_update_multiple_fields(
        self, auth_client: AsyncClient
    ) -> None:
        """Обновление нескольких полей за раз."""

        response = await auth_client.patch(
            '/api/v1/users/me',
            json={
                'first_name': 'Алексей',
                'city': 'Москва',
                'bio': 'Привет, я тест',
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data['first_name'] == 'Алексей'
        assert data['city'] == 'Москва'
        assert data['bio'] == 'Привет, я тест'


# ==============================================================================
# POST /me/change-password
# ==============================================================================
class TestChangePassword:
    """Тесты POST /api/v1/users/me/change-password."""

    async def test_success(
        self, auth_client: AsyncClient, user_data: dict
    ) -> None:
        """Успешная смена пароля."""

        response = await auth_client.post(
            '/api/v1/users/me/change-password',
            json={
                'old_password': user_data['password'],
                'new_password': 'new_strong_password123',
                'new_password_confirm': 'new_strong_password123',
            },
        )
        assert response.status_code == 200
        assert response.json()['message'] == 'Пароль успешно изменен'

    async def test_wrong_old_password(
        self, auth_client: AsyncClient
    ) -> None:
        """Неверный старый пароль → 400."""

        response = await auth_client.post(
            '/api/v1/users/me/change-password',
            json={
                'old_password': 'WRONG_old_password',
                'new_password': 'new_strong_password123',
                'new_password_confirm': 'new_strong_password123',
            },
        )
        assert response.status_code == 400
