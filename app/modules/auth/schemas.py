from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Схема входных данных для логина."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Схема ответа с JWT-токеном."""

    access_token: str
    token_type: str = 'bearer'
