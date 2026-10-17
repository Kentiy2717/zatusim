import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.modules.users.exceptions import (
    UserAuthError,
    UserEmailAlreadyExistsError,
    UserInactiveError,
    UsernameAlreadyExistsError,
)
from app.modules.users.models import User
from app.modules.users.schemas import (
    UserChangePassword,
    UserCreate,
    UserReadPublic,
    UserUpdate,
)


class UserService:
    """Сервис бизнес-логики для работы с профилями пользователей."""

    # ==============================================================================
    # 1. ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЕЙ ИЗ БД
    # ==============================================================================

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        """Возвращает объект пользователя по его ID или None."""

        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        """Возвращает объект пользователя по его email или None."""

        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        """Возвращает объект пользователя по его username или None."""

        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    # ==============================================================================
    # 2. ПРОВЕРКИ И АУТЕНТИФИКАЦИЯ
    # ==============================================================================

    @staticmethod
    def check_active(user: User) -> User:
        """Проверяет активность пользователя. Если деактивирован — выбрасывает доменное исключение."""

        if not user.is_active:
            raise UserInactiveError()
        return user

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
        """Проверяет учетные данные и возвращает активного пользователя."""

        user = await UserService.get_by_email(session, email)
        if not user or not verify_password(password, user.hashed_password):
            raise UserAuthError()

        return UserService.check_active(user)

    # ==============================================================================
    # 3. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
    # ==============================================================================
    @classmethod
    async def create_user(cls, session: AsyncSession, user_in: UserCreate) -> User:
        """Создает нового пользователя с хешированием пароля и проверкой дубликатов."""

        # 1. Проверка email с вызовом доменного исключения
        if await cls.get_by_email(session, user_in.email):
            raise UserEmailAlreadyExistsError()

        # 2. Проверка username с вызовом доменного исключения
        if await cls.get_by_username(session, user_in.username):
            raise UsernameAlreadyExistsError()

        # 3. Безопасная сборка словаря данных
        user_data = user_in.model_dump(
            exclude={'password', 'password_confirm'},
            exclude_unset=True,
        )

        hashed_pwd = get_password_hash(user_in.password)

        # 4. Создание объекта модели
        new_user = User(
            **user_data,
            hashed_password=hashed_pwd,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    # ==============================================================================
    # 4. ОБНОВЛЕНИЕ И РАБОТА С ПРОФИЛЕМ
    # ==============================================================================

    @staticmethod
    async def update_me(
        db: AsyncSession,
        current_user: User,
        update_data: UserUpdate,
    ) -> User:
        """Обновление данных текущего пользователя с проверкой уникальности email и username."""

        update_dict = update_data.model_dump(exclude_unset=True)

        # 1. Проверка уникальности email
        if (
            'email' in update_dict
            and update_dict['email'] != current_user.email
            and await UserService.get_by_email(db, update_dict['email'])
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Этот email уже занят другим пользователем',
                )

        # 2. Проверка уникальности username
        if (
            'username' in update_dict
            and update_dict['username'] != current_user.username
            and await UserService.get_by_username(db, update_dict['username'])
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Этот username уже занят другим пользователем',
                )

        # 3. Применение изменений
        for field, value in update_dict.items():
            if field == 'privacy_settings' and value is not None:
                if hasattr(value, 'model_dump'):
                    setattr(current_user, field, value.model_dump())
                else:
                    setattr(current_user, field, value)
            else:
                setattr(current_user, field, value)

        await db.commit()
        await db.refresh(current_user)
        return current_user

    @staticmethod
    async def get_public_profile(
        db: AsyncSession,
        target_username: str,
    ) -> UserReadPublic:
        """Получение чужого профиля с учетом его настроек приватности."""

        target_user = await UserService.get_by_username(db, target_username)

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Пользователь не найден',
            )

        privacy = target_user.privacy_settings or {}

        # Формируем публичные данные на основе флагов приватности
        user_data = {
            'id': target_user.id,
            'username': target_user.username,
            'first_name': target_user.first_name if privacy.get('show_first_name', True) else 'Аноним',
            'last_name': target_user.last_name if privacy.get('show_last_name', True) else None,
            'gender': target_user.gender,
            'preference': target_user.preference if privacy.get('show_preference', True) else None,
            'avatar_url': target_user.avatar_url,
            'bio': target_user.bio if privacy.get('show_bio', True) else None,
            'birth_date': target_user.birth_date if privacy.get('show_birth_year', True) else None,
            'city': target_user.city if privacy.get('show_city', True) else None,
            'phone': target_user.phone if privacy.get('show_phone', False) else None,
            'vk_link': target_user.vk_link if privacy.get('show_vk', True) else None,
            'party_status': target_user.party_status,
        }

        return UserReadPublic.model_validate(user_data)

    @staticmethod
    async def change_password(
        db: AsyncSession,
        current_user: User,
        password_data: UserChangePassword,
    ) -> None:
        """Безопасная смена пароля с проверкой старого пароля."""

        if not verify_password(password_data.old_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Неверный текущий пароль',
            )

        current_user.hashed_password = get_password_hash(password_data.new_password)
        await db.commit()

    @staticmethod
    async def upload_avatar(
        db: AsyncSession,
        current_user: User,
        file: UploadFile,
    ) -> User:
        """Загрузка файла аватарки на диск и сохранение ссылки в профиль."""

        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Загружаемый файл должен быть изображением (jpeg, png, webp)',
            )

        upload_dir = Path('uploads/avatars')
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 1. Удаляем старую аватарку, если она существует
        if current_user.avatar_url:
            # Превращаем URL (/uploads/avatars/file.jpg) в путь к файлу и безопасно удаляем
            old_file_path = Path(current_user.avatar_url.lstrip('/'))
            old_file_path.unlink(missing_ok=True)

        file_extension = Path(file.filename).suffix if file.filename else '.png'
        file_name = f'user_{current_user.id}_{uuid.uuid4().hex[:8]}{file_extension}'
        file_path = upload_dir / file_name

        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        current_user.avatar_url = f'/uploads/avatars/{file_name}'
        await db.commit()
        await db.refresh(current_user)
        return current_user
