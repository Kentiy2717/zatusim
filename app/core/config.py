from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = 'Zatusim'
    DEBUG: bool = True
    SECRET_KEY: str = 'super-secret-key-change-in-production-12345'

    POSTGRES_SERVER: str = 'localhost'
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_DB: str = 'zatusim_db'

    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379

    BACKEND_CORS_ORIGINS: list[str] | str = [
        'http://localhost:8081',
        'http://localhost:8004',
        'http://127.0.0.1:8081',
        'http://127.0.0.1:8004',
    ]

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True,
    )

    @property
    def database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(',') if i.strip()]
        if isinstance(v, list):
            return v
        raise ValueError(v)


settings = Settings()
