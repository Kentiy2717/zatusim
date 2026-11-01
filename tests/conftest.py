"""
Общие фикстуры для всех тестов проекта.

Архитектура:
  - setup_database: создаёт таблицы ОДИН РАЗ на весь прогон (session scope)
  - clean_database: очищает таблицы ПЕРЕД каждым тестом (autouse)
  - db: асинхронная сессия к тестовой БД
  - client: HTTP-клиент с подменённой БД (dependency_overrides)
  - user_data: стандартные данные для регистрации
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.db.base import Base  # ← импортирует ВСЕ модели (User, Friendship, ...)
from app.db.session import get_db_session
from app.main import app

# ==============================================================================
# 1. ТЕСТОВЫЙ ДВИЖОК БД
# ==============================================================================
# Берём URL из переменной окружения или используем дефолт (localhost:5433)
TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql+asyncpg://postgres:postgres@localhost:5433/test_zatusim_db',
)

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==============================================================================
# 2. СОЗДАНИЕ / УДАЛЕНИЕ ТАБЛИЦ (один раз на весь прогон)
# ==============================================================================
@pytest.fixture(scope='session', autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """
    Создаёт все таблицы в тестовой БД перед прогоном тестов
    и удаляет их после. Работает один раз (scope='session').
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ==============================================================================
# 3. ОЧИСТКА ТАБЛИЦ (перед каждым тестом)
# ==============================================================================
@pytest.fixture(autouse=True)
async def clean_database() -> AsyncGenerator[None, None]:
    """
    Удаляет все записи из всех таблиц ПЕРЕД каждым тестом.
    """

    # Очищаем ПЕРЕД тестом (чтобы мусор от предыдущего не мешал)
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    yield


# ==============================================================================
# 4. СЕССИЯ БД
# ==============================================================================
@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная сессия к тестовой БД.
    """

    async with TestSessionLocal() as session:
        yield session


# ==============================================================================
# 5. HTTP-КЛИЕНТ (с подменённой БД)
# ==============================================================================
@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Асинхронный HTTP-клиент для тестирования роутов.

    Подменяет зависимость get_db_session так, чтобы все запросы
    шли в тестовую БД, а не в продакшн.

    НЕ запускает uvicorn — вызывает FastAPI-приложение напрямую
    через ASGI-transport httpx.
    """

    # Подмена зависимости: FastAPI будет отдавать тестовую сессию
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db_session] = override_get_db

    # Создаём клиент, привязанный к нашему приложению
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

    # После теста убираем подмену
    app.dependency_overrides.clear()


# ==============================================================================
# 6. ТЕСТОВЫЕ ДАННЫЕ
# ==============================================================================
@pytest.fixture
def user_data() -> dict:
    """
    Стандартные данные для регистрации тестового пользователя.
    """

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
    """
    Фабрика для создания уникальных данных пользователя.
    """

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