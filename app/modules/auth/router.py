from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.core.security import create_access_token
from app.modules.auth.schemas import LoginRequest, Token
from app.modules.users.exceptions import UserAuthError, UserInactiveError
from app.modules.users.service import authenticate_user

router = APIRouter()


@router.post(
    '/login',
    response_model=Token,
    summary='Аутентификация пользователя и получение JWT-токена',
)
async def login(
    login_in: LoginRequest,
    session: DbSession,
) -> Token:
    """Проверяет учетные данные и возвращает JWT Access Token."""

    try:
        user = await authenticate_user(session, login_in.email, login_in.password)
    except UserAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неверный email или пароль.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    except UserInactiveError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Учетная запись деактивирована.',
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)
