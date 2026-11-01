"""
Интеграционные тесты авторизации (register + login).
"""

from httpx import AsyncClient


# ==============================================================================
# РЕГИСТРАЦИЯ
# ==============================================================================
class TestRegister:
    """Тесты POST /api/v1/auth/register."""

    async def test_success(self, client: AsyncClient, user_data: dict) -> None:
        """
        Успешная регистрация.

        Что проверяем:
          - Статус 201 (Created)
          - В ответе есть id, email, first_name
          - В ответе НЕТ паролей
        """

        response = await client.post('/api/v1/auth/register', json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data['email'] == user_data['email']
        assert data['first_name'] == user_data['first_name']
        assert 'id' in data
        assert 'password' not in data
        assert 'hashed_password' not in data

    async def test_duplicate_email(
        self, client: AsyncClient, user_data: dict, user_data_factory
    ) -> None:
        """
        Дубликат email → 400.

        Что проверяем:
          - Первый регистр проходит
          - Второй с тем же email → 400 + понятное сообщение
        """

        # Первый пользователь
        r1 = await client.post('/api/v1/auth/register', json=user_data)
        assert r1.status_code == 201

        # Второй с тем же email, но другим username
        user2 = user_data_factory(
            email=user_data['email'],
            username='another_username',
        )
        r2 = await client.post('/api/v1/auth/register', json=user2)
        assert r2.status_code == 400
        assert 'email' in r2.json()['detail'].lower()

    async def test_duplicate_username(
        self, client: AsyncClient, user_data: dict, user_data_factory
    ) -> None:
        """Дубликат username → 400."""

        r1 = await client.post('/api/v1/auth/register', json=user_data)
        assert r1.status_code == 201

        user2 = user_data_factory(
            username=user_data['username'],
            email='another@example.com',
        )
        r2 = await client.post('/api/v1/auth/register', json=user2)
        assert r2.status_code == 400
        assert 'username' in r2.json()['detail'].lower()

    async def test_invalid_data(self, client: AsyncClient) -> None:
        """
        Невалидные данные → 422 (Unprocessable Entity).
        """

        response = await client.post('/api/v1/auth/register', json={
            'email': 'не-email',
            'password': '123',
        })
        assert response.status_code == 422


# ==============================================================================
# ЛОГИН
# ==============================================================================
class TestLogin:
    """Тесты POST /api/v1/auth/login."""

    async def test_success(self, client: AsyncClient, user_data: dict) -> None:
        """
        Успешный логин → JWT-токен.
        """

        # Регистрируем
        await client.post('/api/v1/auth/register', json=user_data)

        # Логинимся
        response = await client.post('/api/v1/auth/login', json={
            'email': user_data['email'],
            'password': user_data['password'],
        })

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'

    async def test_wrong_password(
        self, client: AsyncClient, user_data: dict
    ) -> None:
        """Неверный пароль → 401."""

        await client.post('/api/v1/auth/register', json=user_data)

        response = await client.post('/api/v1/auth/login', json={
            'email': user_data['email'],
            'password': 'WRONG_password',
        })
        assert response.status_code == 401
        assert 'Неверный' in response.json()['detail']

    async def test_nonexistent_user(self, client: AsyncClient) -> None:
        """Несуществующий пользователь → 401."""

        response = await client.post('/api/v1/auth/login', json={
            'email': 'ghost@example.com',
            'password': 'any_password',
        })
        assert response.status_code == 401
