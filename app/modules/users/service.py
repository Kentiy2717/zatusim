from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password
from app.modules.users.exceptions import UserAuthError, UserInactiveError
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate


def check_user_active(user: User) -> User:
    """Проверяет активность пользователя. Если деактивирован — выбрасывает доменное исключение."""
    if not user.is_active:
        raise UserInactiveError()
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Возвращает объект пользователя по его ID или None."""

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Возвращает объект пользователя по его email или None."""

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    """Проверяет учетные данные и возвращает активного пользователя."""

    user = await get_user_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        raise UserAuthError()

    return check_user_active(user)


async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    """Создает нового пользователя с хешированием пароля и сохранением в БД."""

    hashed_pwd = get_password_hash(user_in.password)

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        gender=user_in.gender,
        preference=user_in.preference,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user
