from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.core.security import create_access_token
from app.modules.auth.schemas import LoginRequest, Token
from app.modules.users.exceptions import (
    UserAuthError,
    UserEmailAlreadyExistsError,
    UserInactiveError,
    UsernameAlreadyExistsError,
)
from app.modules.users.schemas import UserCreate, UserReadMe
from app.modules.users.service import UserService

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post(
    '/register',
    response_model=UserReadMe,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
async def register(
    user_in: UserCreate,
    session: DbSession,
) -> UserReadMe:
    """Регистрирует нового пользователя в системе."""

    try:
        return await UserService.create_user(session=session, user_in=user_in)
    except UserEmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким email уже существует',
        )
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким username уже существует',
        )


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
        user = await UserService.authenticate_user(
            session=session,
            email=login_in.email,
            password=login_in.password,
        )
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

    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token)
