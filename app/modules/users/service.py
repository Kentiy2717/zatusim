from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Возвращает объект пользователя по его email или None."""

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


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
