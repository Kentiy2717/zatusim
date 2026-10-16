from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.modules.users.schemas import UserCreate, UserRead
from app.modules.users.service import create_user, get_user_by_email

router = APIRouter()


@router.post(
    '/register',
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация нового пользователя',
)
async def register_user(
    user_in: UserCreate,
    session: DbSession,
) -> UserRead:
    """Регистрирует нового пользователя в системе.

    Проверяет уникальность email и возвращает созданного пользователя без пароля.
    """
    existing_user = await get_user_by_email(session, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким email уже зарегистрирован.',
        )

    new_user = await create_user(session, user_in)
    return new_user
