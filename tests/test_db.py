from app.core.config import settings


def test_settings_load() -> None:
    """Проверка корректной загрузки настроек из файла .env."""
    assert settings.PROJECT_NAME == 'Zatusim'
    assert 'postgresql+asyncpg://' in settings.database_url
