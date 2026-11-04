"""Общие фикстуры для всех тестов проекта.

Архитектура:
  - tests/db.py: тестовый движок и фабрика сессий (общие для всех слоёв)
  - tests/integration/conftest.py: фикстуры с autouse (создание/очистка таблиц)
  - tests/conftest.py: db, client и тестовые данные — доступны всем слоям

Юнит-тесты (tests/unit) работают на моках и НЕ требуют живую БД:
фикстуры с autouse=True объявлены только в интеграционном conftest.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.main import app
from tests.db import TestSessionLocal


# ==============================================================================
# 1. СЕССИЯ БД
# ==============================================================================
@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная сессия к тестовой БД."""

    async with TestSessionLocal() as session:
        yield session


# ==============================================================================
# 2. HTTP-КЛИЕНТ (с подменённой БД)
# ==============================================================================
@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный HTTP-клиент для тестирования роутов.

    Подменяет зависимость get_db_session так, чтобы все запросы
    шли в тестовую БД, а не в продакшн.

    НЕ запускает uvicorn — вызывает FastAPI-приложение напрямую
    через ASGI-transport httpx.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

    app.dependency_overrides.clear()


# ==============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# ==============================================================================
@pytest.fixture
def user_data() -> dict:
    """Стандартные данные для регистрации тестового пользователя."""

    return {
        'email': 'test_user@example.com',
        'password': 'strongpassword123',
        'password_confirm': 'strongpassword123',
        'username': 'test_user_ivan',
        'first_name': 'Иван',
        'last_name': 'Иванович',
        'gender': 'M',
        'preference': 'F',
        'birth_date': '1995-05-15',
    }


@pytest.fixture
def user_data_factory():
    """Фабрика для создания уникальных данных пользователя."""

    def _create(**overrides) -> dict:
        defaults = {
            'email': 'factory_user@example.com',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123',
            'username': 'factory_user',
            'first_name': 'Фабрика',
            'gender': 'M',
            'preference': 'F',
            'birth_date': '1995-05-15',
        }
        defaults.update(overrides)
        return defaults

    return _create
