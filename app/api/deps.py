from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.modules.users.exceptions import UserInactiveError
from app.modules.users.models import User
from app.modules.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    session: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Dependency: расшифровывает JWT и возвращает объект текущего пользователя."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Не удалось валидировать учетные данные.',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get('sub')
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = await UserService.get_by_id(session, user_id)
    if user is None:
        raise credentials_exception

    try:
        return UserService.check_active(user)
    except UserInactiveError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Учетная запись деактивирована.',
        )


CurrentUser = Annotated[User, Depends(get_current_user)]
