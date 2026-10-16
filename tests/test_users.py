import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import AsyncSessionLocal
from app.modules.users.models import User


def delete_user_by_email(email: str) -> None:
    """Удаляет пользователя из БД по email после теста."""

    async def _cleanup() -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(User).where(User.email == email))
            await session.commit()

    asyncio.run(_cleanup())


def test_register_user_success(client: TestClient) -> None:
    """Тест успешной регистрации + очистка пользователя из БД."""

    user_data = {
        'email': 'test_user@example.com',
        'password': 'strongpassword123',
        'first_name': 'Иван',
        'last_name': 'Иванович',
        'gender': 'M',
        'preference': 'F',
    }

    try:
        response = client.post('/api/v1/users/register', json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data['email'] == user_data['email']
        assert data['first_name'] == user_data['first_name']
        assert 'id' in data
        assert 'password' not in data
        assert 'hashed_password' not in data
    finally:
        delete_user_by_email(user_data['email'])


def test_register_user_duplicate_email(client: TestClient) -> None:
    """Тест ошибки при попытке зарегистрировать дубликат email + очистка."""

    user_data = {
        'email': 'duplicate@example.com',
        'password': 'password123',
        'first_name': 'Иван',
        'gender': 'M',
        'preference': 'F',
    }

    try:
        first_response = client.post('/api/v1/users/register', json=user_data)
        assert first_response.status_code == 201

        second_response = client.post('/api/v1/users/register', json=user_data)
        assert second_response.status_code == 400
        assert second_response.json()['detail'] == (
            'Пользователь с таким email уже зарегистрирован.'
        )
    finally:
        delete_user_by_email(user_data['email'])
