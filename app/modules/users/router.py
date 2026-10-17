from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.modules.users.models import User
from app.modules.users.schemas import (
    UserChangePassword,
    UserReadMe,
    UserReadPublic,
    UserUpdate,
)
from app.modules.users.service import UserService

router = APIRouter(prefix='/users', tags=['Users'])


@router.get(
    '/me',
    response_model=UserReadMe,
    summary='Получить данные текущего пользователя',
)
async def get_me(
    current_user: CurrentUser,
) -> User:
    """Возвращает полный профиль авторизованного пользователя, включая приватные данные."""
    return current_user


@router.patch(
    '/me',
    response_model=UserReadMe,
    summary='Частично обновить свой профиль',
)
async def update_me(
    update_data: UserUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> User:
    """Обновляет переданные поля профиля или настройки приватности текущего пользователя."""
    return await UserService.update_me(
        db=session,
        current_user=current_user,
        update_data=update_data,
    )


@router.post(
    '/me/avatar',
    response_model=UserReadMe,
    summary='Загрузить аватар профиля',
)
async def upload_avatar(
    session: DbSession,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File()],
) -> User:
    """Загружает файл изображения, удаляет старую аватарку и сохраняет новый путь."""

    return await UserService.upload_avatar(
        db=session,
        current_user=current_user,
        file=file,
    )


@router.post(
    '/me/change-password',
    status_code=status.HTTP_200_OK,
    summary='Сменить пароль',
)
async def change_password(
    data: UserChangePassword,
    session: DbSession,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Проверяет старый пароль и устанавливает новый."""

    await UserService.change_password(
        db=session,
        current_user=current_user,
        password_data=data,
    )
    return {'message': 'Пароль успешно изменен'}


@router.get(
    '/{username}',
    response_model=UserReadPublic,
    summary='Просмотр публичного профиля пользователя',
)
async def get_public_profile(
    username: str,
    session: DbSession,
    current_user: CurrentUser,
) -> UserReadPublic:
    """Возвращает публичный профиль пользователя по его `username` с фильтрацией закрытых полей."""

    return await UserService.get_public_profile(
        db=session,
        target_username=username,
    )
