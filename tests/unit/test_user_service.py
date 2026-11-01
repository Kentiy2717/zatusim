"""
Юнит-тесты UserService с моками.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.users.exceptions import (
    UserAuthError,
    UserEmailAlreadyExistsError,
    UserInactiveError,
)
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


# ==============================================================================
# ФИКСТУРЫ
# ==============================================================================
@pytest.fixture
def fake_user() -> User:
    """
    Stub: фейковый ORM-объект пользователя.
    """

    user = MagicMock(spec=User)
    user.id = 1
    user.email = 'test@example.com'
    user.username = 'testuser'
    user.first_name = 'Иван'
    user.hashed_password = '$2b$12$fakehash'
    user.is_active = True
    return user


@pytest.fixture
def mock_session() -> AsyncMock:
    """
    Мок асинхронной сессии БД.
    """

    session = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


# ==============================================================================
# create_user — с @patch
# ==============================================================================
class TestCreateUser:
    """
    Тесты UserService.create_user с моками.
    """

    @pytest.mark.asyncio
    @patch.object(UserService, 'get_by_email', new_callable=AsyncMock)
    @patch.object(UserService, 'get_by_username', new_callable=AsyncMock)
    async def test_success(
        self,
        mock_get_username: AsyncMock,
        mock_get_email: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """
        Успешное создание пользователя.
        """

        mock_get_email.return_value = None
        mock_get_username.return_value = None

        user_in = UserCreate(
            email='new@example.com',
            password='strongpass123',
            password_confirm='strongpass123',
            username='newuser',
            first_name='Новый',
            birth_date='1995-05-15',
            gender='M',
            preference='F',
        )

        await UserService.create_user(
            session=mock_session,
            user_in=user_in,
        )

        # Проверяем, что сессия использовалась
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(UserService, 'get_by_email', new_callable=AsyncMock)
    async def test_duplicate_email(
        self,
        mock_get_email: AsyncMock,
        mock_session: AsyncMock,
        fake_user: User,
    ) -> None:
        """
        Дубликат email → UserEmailAlreadyExistsError.
        """

        mock_get_email.return_value = fake_user

        user_in = UserCreate(
            email='test@example.com',
            password='strongpass123',
            password_confirm='strongpass123',
            username='newuser',
            first_name='Новый',
            birth_date='1995-05-15',
            gender='M',
            preference='F',
        )

        with pytest.raises(UserEmailAlreadyExistsError):
            await UserService.create_user(session=mock_session, user_in=user_in)

        # Проверяем, что до сохранения не дошло
        mock_session.add.assert_not_called()


# ==============================================================================
# authenticate_user — с monkeypatch
# ==============================================================================
class TestAuthenticateUser:
    """
    Тесты UserService.authenticate_user.
    """

    @pytest.mark.asyncio
    async def test_success(
        self,
        mock_session: AsyncMock,
        fake_user: User,
        monkeypatch,
    ) -> None:
        """
        Верный пароль → возвращает пользователя.
        """

        async def fake_get_email(session, email):
            return fake_user

        monkeypatch.setattr(UserService, 'get_by_email', fake_get_email)

        # Подменяем verify_password
        monkeypatch.setattr(
            'app.modules.users.service.verify_password',
            lambda plain, hashed: True,
        )

        result = await UserService.authenticate_user(
            session=mock_session,
            email='test@example.com',
            password='anypassword',
        )

        assert result == fake_user

    @pytest.mark.asyncio
    async def test_wrong_password(
        self,
        mock_session: AsyncMock,
        fake_user: User,
        monkeypatch,
    ) -> None:
        """Неверный пароль → UserAuthError."""

        async def fake_get_email(session, email):
            return fake_user

        monkeypatch.setattr(UserService, 'get_by_email', fake_get_email)
        monkeypatch.setattr(
            'app.modules.users.service.verify_password',
            lambda plain, hashed: False,
        )

        with pytest.raises(UserAuthError):
            await UserService.authenticate_user(
                session=mock_session,
                email='test@example.com',
                password='wrongpassword',
            )

    @pytest.mark.asyncio
    async def test_user_not_found(
        self,
        mock_session: AsyncMock,
        monkeypatch,
    ) -> None:
        """Пользователь не найден → UserAuthError."""

        async def fake_get_email(session, email):
            return None  # ← юзера нет

        monkeypatch.setattr(UserService, 'get_by_email', fake_get_email)

        with pytest.raises(UserAuthError):
            await UserService.authenticate_user(
                session=mock_session,
                email='ghost@example.com',
                password='anypassword',
            )


# ==============================================================================
# check_active — без моков (чистый юнит)
# ==============================================================================
class TestCheckActive:
    """
    Тесты UserService.check_active.
    """

    def test_active_user(self, fake_user: User) -> None:
        """Активный юзер → возвращает того же юзера."""

        fake_user.is_active = True
        result = UserService.check_active(fake_user)
        assert result == fake_user

    def test_inactive_user(self, fake_user: User) -> None:
        """Неактивный юзер → UserInactiveError."""

        fake_user.is_active = False
        with pytest.raises(UserInactiveError):
            UserService.check_active(fake_user)


# ==============================================================================
# SPY — проверка вызова реальной функции
# ==============================================================================
class TestSpyExample:
    """
    Пример мока функции хеширования
    """

    @pytest.mark.asyncio
    @patch.object(UserService, 'get_by_email', new_callable=AsyncMock)
    @patch.object(UserService, 'get_by_username', new_callable=AsyncMock)
    @patch('app.modules.users.service.get_password_hash')
    async def test_spy_on_hash(
        self,
        spy_hash: MagicMock,
        mock_get_username: AsyncMock,
        mock_get_email: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """
        Spy на get_password_hash.

        Что проверяем:
          - get_password_hash была вызвана ровно 1 раз
          - С правильным аргументом (сырой пароль)
        """

        mock_get_email.return_value = None
        mock_get_username.return_value = None
        spy_hash.return_value = '$2b$12$fake_hashed_password'

        user_in = UserCreate(
            email='spy@example.com',
            password='my_secret_password',
            password_confirm='my_secret_password',
            username='spyuser',
            first_name='Шпион',
            birth_date='1995-05-15',
            gender='M',
            preference='F',
        )

        await UserService.create_user(session=mock_session, user_in=user_in)

        spy_hash.assert_called_once_with('my_secret_password')
