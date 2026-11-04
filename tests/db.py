"""Тестовый движок БД и фабрика сессий.

Вынесено из ``tests/conftest.py``, чтобы фикстуры интеграционного слоя могли
импортировать движок без обращения к conftest по имени модуля.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# URL берём из переменной окружения (CI подставляет её явно)
# или используем локальный дефолт: docker-compose.test.yml → порт 5433
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
