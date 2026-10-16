from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """Базовая Pydantic-схема проекта с поддержкой чтения ORM-атрибутов."""

    model_config = ConfigDict(from_attributes=True)
