"""Фикстуры интеграционных тестов: подготовка и очистка тестовой БД.

Вынесены из корневого ``tests/conftest.py`` намеренно: юнит-тесты
(``tests/unit``) работают на моках и не должны требовать живую PostgreSQL.
Поэтому фикстуры с ``autouse=True`` объявлены только для интеграционного слоя.
"""

from collections.abc import AsyncGenerator

import pytest

from app.db.base import Base  # импортирует ВСЕ модели (User, Friendship, Block, ...)
from tests.db import engine


# ==============================================================================
# 1. СОЗДАНИЕ / УДАЛЕНИЕ ТАБЛИЦ (один раз на весь прогон)
# ==============================================================================
@pytest.fixture(scope='session', autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Создаёт все таблицы в тестовой БД до прогона и удаляет их после."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ==============================================================================
# 2. ОЧИСТКА ТАБЛИЦ (перед каждым тестом)
# ==============================================================================
@pytest.fixture(autouse=True)
async def clean_database() -> AsyncGenerator[None, None]:
    """Удаляет все записи из всех таблиц перед каждым интеграционным тестом."""

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    yield
