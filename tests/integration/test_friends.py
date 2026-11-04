"""Интеграционные тесты модуля друзей: заявки, чёрный список, поиск.

Тесты работают через реальные HTTP-вызовы и реального текущего пользователя
(JWT), чтобы проверить каноническое хранение пары ``user_id < friend_id``
и корректную подстановку ``other_user`` для обеих сторон.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService


# ==============================================================================
# ФИКСТУРЫ: ДВА ПОЛНОЦЕННЫХ ПОЛЬЗОВАТЕЛЯ
# ==============================================================================
@pytest.fixture
async def two_users(db, user_data_factory) -> tuple[User, User]:
    """Создаёт двух пользователей напрямую через сервис."""

    ivan = await UserService.create_user(
        session=db,
        user_in=UserCreate(**user_data_factory(
            email='ivan@example.com', username='ivan_94', first_name='Иван',
        )),
    )
    masha = await UserService.create_user(
        session=db,
        user_in=UserCreate(**user_data_factory(
            email='masha@example.com', username='masha_95', first_name='Маша',
        )),
    )
    return ivan, masha


@pytest.fixture
async def pair(two_users: tuple[User, User]) -> tuple[User, User]:
    """Пара пользователей: (иван, маша)."""

    return two_users


@pytest.fixture
async def ivan_client(client: AsyncClient, pair) -> AsyncGenerator[AsyncClient, None]:
    """Клиент с авторизацией за первого пользователя."""

    from app.api.deps import get_current_user
    from app.main import app

    ivan, _ = pair

    async def override() -> User:
        return ivan

    app.dependency_overrides[get_current_user] = override
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def masha_client(client: AsyncClient, pair) -> AsyncGenerator[AsyncClient, None]:
    """Клиент с авторизацией за второго пользователя."""

    from app.api.deps import get_current_user
    from app.main import app

    _, masha = pair

    async def override() -> User:
        return masha

    app.dependency_overrides[get_current_user] = override
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# 1. ОТПРАВКА ЗАЯВКИ
# ==============================================================================
class TestSendRequest:
    """POST /api/v1/friends/requests"""

    async def test_success_returns_201_and_pair_is_canonical(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Заявка создаётся, пара хранится в каноническом виде."""

        ivan, masha = pair
        response = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': masha.id}
        )

        assert response.status_code == 201
        data = response.json()
        assert data['status'] == 'pending'
        assert data['initiator_id'] == ivan.id
        assert data['initiated_by_me'] is True
        assert data['other_user']['username'] == masha.username
        # Канонический порядок: user_id всегда меньше friend_id
        assert data['user']['id'] == min(ivan.id, masha.id)
        assert data['friend']['id'] == max(ivan.id, masha.id)

    async def test_by_username(self, ivan_client: AsyncClient, pair) -> None:
        """Заявку можно отправить по username."""

        _, masha = pair
        response = await ivan_client.post(
            '/api/v1/friends/requests', json={'username': masha.username}
        )

        assert response.status_code == 201
        assert response.json()['other_user']['id'] == masha.id

    async def test_requires_exactly_one_identifier(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Без идентификатора или с обоими сразу — 422."""

        _, masha = pair

        empty = await ivan_client.post('/api/v1/friends/requests', json={})
        assert empty.status_code == 422

        both = await ivan_client.post(
            '/api/v1/friends/requests',
            json={'username': masha.username, 'user_id': masha.id},
        )
        assert both.status_code == 422

    async def test_self_request_returns_400(self, ivan_client: AsyncClient, pair) -> None:
        """Нельзя добавить в друзья самого себя."""

        ivan, _ = pair
        response = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': ivan.id}
        )

        assert response.status_code == 400
        assert 'самого себя' in response.json()['detail']

    async def test_unknown_user_returns_404(self, ivan_client: AsyncClient) -> None:
        """Несуществующий пользователь — 404."""

        response = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': 999999}
        )

        assert response.status_code == 404

    async def test_duplicate_request_returns_400(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Повторная отправка той же заявки — 400."""

        _, masha = pair
        payload = {'user_id': masha.id}

        first = await ivan_client.post('/api/v1/friends/requests', json=payload)
        assert first.status_code == 201

        second = await ivan_client.post('/api/v1/friends/requests', json=payload)
        assert second.status_code == 400
        assert 'уже отправлена' in second.json()['detail']

    async def test_counter_request_auto_accepts(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Встречная заявка принимается автоматически."""

        ivan, masha = pair

        first = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': masha.id}
        )
        assert first.status_code == 201

        counter = await masha_client.post(
            '/api/v1/friends/requests', json={'user_id': ivan.id}
        )
        assert counter.status_code == 201
        assert counter.json()['status'] == 'accepted'

        friends = await ivan_client.get('/api/v1/friends')
        assert friends.status_code == 200
        assert len(friends.json()) == 1


# ==============================================================================
# 2. СПИСКИ
# ==============================================================================
class TestLists:
    """Списки друзей, входящих и исходящих заявок."""

    async def test_incoming_and_outgoing_are_perspective_aware(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """У каждой стороны свой список и свой other_user."""

        ivan, masha = pair
        await ivan_client.post('/api/v1/friends/requests', json={'user_id': masha.id})

        ivan_outgoing = await ivan_client.get('/api/v1/friends/requests/outgoing')
        ivan_incoming = await ivan_client.get('/api/v1/friends/requests/incoming')
        masha_incoming = await masha_client.get('/api/v1/friends/requests/incoming')
        masha_outgoing = await masha_client.get('/api/v1/friends/requests/outgoing')

        assert len(ivan_outgoing.json()) == 1
        assert ivan_outgoing.json()[0]['other_user']['id'] == masha.id
        assert ivan_outgoing.json()[0]['initiated_by_me'] is True
        assert len(ivan_incoming.json()) == 0

        assert len(masha_incoming.json()) == 1
        assert masha_incoming.json()[0]['other_user']['id'] == ivan.id
        assert masha_incoming.json()[0]['initiated_by_me'] is False
        assert len(masha_outgoing.json()) == 0

        # До принятия список друзей пуст у обоих
        assert (await ivan_client.get('/api/v1/friends')).json() == []

    async def test_friends_list_after_accept(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """После принятия оба видят друг друга в друзьях."""

        ivan, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']

        accepted = await masha_client.post(
            f'/api/v1/friends/requests/{request_id}/accept'
        )
        assert accepted.status_code == 200
        assert accepted.json()['status'] == 'accepted'

        for client_, other in ((ivan_client, masha), (masha_client, ivan)):
            friends = await client_.get('/api/v1/friends')
            assert friends.status_code == 200
            body = friends.json()
            assert len(body) == 1
            assert body[0]['other_user']['username'] == other.username


# ==============================================================================
# 3. ПРИНЯТИЕ / ОТКЛОНЕНИЕ / ОТЗЫВ / УДАЛЕНИЕ
# ==============================================================================
class TestRequestActions:
    """Действия над заявками и дружбой."""

    async def test_accept_own_request_returns_404(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Собственную заявку принять нельзя."""

        _, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']

        response = await ivan_client.post(
            f'/api/v1/friends/requests/{request_id}/accept'
        )
        assert response.status_code == 404

    async def test_decline_blocks_resend(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Отклонённую заявку нельзя отправить повторно."""

        _, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']

        declined = await masha_client.post(
            f'/api/v1/friends/requests/{request_id}/decline'
        )
        assert declined.status_code == 204

        # У Маши заявка исчезла из входящих
        assert (await masha_client.get('/api/v1/friends/requests/incoming')).json() == []

        # Повторная отправка запрещена
        again = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': masha.id}
        )
        assert again.status_code == 400
        assert 'отклонена' in again.json()['detail']

        # Состояние связи отражает отказ
        relation = await ivan_client.get(f'/api/v1/friends/relation/{masha.id}')
        assert relation.json()['is_declined'] is True
        assert relation.json()['is_friend'] is False

    async def test_cancel_outgoing_request(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Инициатор может отозвать свою заявку."""

        _, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']

        cancelled = await ivan_client.delete(f'/api/v1/friends/requests/{request_id}')
        assert cancelled.status_code == 204

        assert (await ivan_client.get('/api/v1/friends/requests/outgoing')).json() == []
        assert (await masha_client.get('/api/v1/friends/requests/incoming')).json() == []

        # После отзыва заявку можно отправить заново
        again = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': masha.id}
        )
        assert again.status_code == 201

    async def test_remove_friend(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Удаление из друзей разрывает связь у обеих сторон."""

        _, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']
        await masha_client.post(f'/api/v1/friends/requests/{request_id}/accept')

        removed = await ivan_client.delete(f'/api/v1/friends/{masha.id}')
        assert removed.status_code == 204

        assert (await ivan_client.get('/api/v1/friends')).json() == []
        assert (await masha_client.get('/api/v1/friends')).json() == []

        second = await ivan_client.delete(f'/api/v1/friends/{masha.id}')
        assert second.status_code == 404


# ==============================================================================
# 4. ЧЁРНЫЙ СПИСОК
# ==============================================================================
class TestBlocks:
    """Блокировки и их влияние на заявки."""

    async def test_block_breaks_friendship(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Блокировка удаляет существующую дружбу."""

        _, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']
        await masha_client.post(f'/api/v1/friends/requests/{request_id}/accept')

        blocked = await ivan_client.post(
            '/api/v1/friends/blocks', json={'user_id': masha.id}
        )
        assert blocked.status_code == 201
        assert blocked.json()['blocked']['id'] == masha.id

        assert (await ivan_client.get('/api/v1/friends')).json() == []
        assert (await masha_client.get('/api/v1/friends')).json() == []

        blocks = await ivan_client.get('/api/v1/friends/blocks')
        assert len(blocks.json()) == 1

    async def test_blocked_user_cannot_send_request(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Заблокированный пользователь получает 404 (факт блока не раскрываем)."""

        _, masha = pair
        await ivan_client.post('/api/v1/friends/blocks', json={'user_id': masha.id})

        ivan, _ = pair
        response = await masha_client.post(
            '/api/v1/friends/requests', json={'user_id': ivan.id}
        )
        assert response.status_code == 404

    async def test_request_to_blocked_user_returns_400(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Нельзя отправить заявку тому, кого сам заблокировал."""

        _, masha = pair
        await ivan_client.post('/api/v1/friends/blocks', json={'user_id': masha.id})

        response = await ivan_client.post(
            '/api/v1/friends/requests', json={'user_id': masha.id}
        )
        assert response.status_code == 400
        assert 'разблокируйте' in response.json()['detail'].lower()

    async def test_duplicate_block_and_unblock(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Повторный блок — 400, разблокировка — 204, повторная — 404."""

        _, masha = pair

        first = await ivan_client.post(
            '/api/v1/friends/blocks', json={'user_id': masha.id}
        )
        assert first.status_code == 201

        duplicate = await ivan_client.post(
            '/api/v1/friends/blocks', json={'user_id': masha.id}
        )
        assert duplicate.status_code == 400

        unblocked = await ivan_client.delete(f'/api/v1/friends/blocks/{masha.id}')
        assert unblocked.status_code == 204
        assert (await ivan_client.get('/api/v1/friends/blocks')).json() == []

        again = await ivan_client.delete(f'/api/v1/friends/blocks/{masha.id}')
        assert again.status_code == 404

    async def test_block_self_returns_400(self, ivan_client: AsyncClient, pair) -> None:
        """Заблокировать себя нельзя."""

        ivan, _ = pair
        response = await ivan_client.post(
            '/api/v1/friends/blocks', json={'user_id': ivan.id}
        )
        assert response.status_code == 400


# ==============================================================================
# 5. ПОИСК И СОСТОЯНИЕ СВЯЗИ
# ==============================================================================
class TestSearchAndRelation:
    """GET /api/v1/users/search и GET /api/v1/friends/relation/{id}"""

    async def test_search_finds_by_username_with_relation(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Поиск находит пользователя и отдаёт состояние связи."""

        _, masha = pair

        response = await ivan_client.get('/api/v1/users/search', params={'q': 'masha'})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]['username'] == masha.username
        assert body[0]['relation'] is None or body[0]['relation']['is_friend'] is False

        # После заявки статус связи появляется в выдаче
        await ivan_client.post('/api/v1/friends/requests', json={'user_id': masha.id})
        second = await ivan_client.get('/api/v1/users/search', params={'q': 'masha'})
        relation = second.json()[0]['relation']
        assert relation['is_outgoing_request'] is True
        assert relation['status'] == 'pending'

    async def test_search_does_not_return_self(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Себя в выдаче нет."""

        ivan, _ = pair
        response = await ivan_client.get('/api/v1/users/search', params={'q': 'ivan'})

        assert response.status_code == 200
        assert all(item['id'] != ivan.id for item in response.json())

    async def test_search_requires_min_length(self, ivan_client: AsyncClient) -> None:
        """Запрос короче двух символов — 422."""

        response = await ivan_client.get('/api/v1/users/search', params={'q': 'a'})
        assert response.status_code == 422

    async def test_relation_endpoint(
        self, ivan_client: AsyncClient, masha_client: AsyncClient, pair
    ) -> None:
        """Сводка состояния связи для обеих сторон."""

        ivan, masha = pair
        request_id = (
            await ivan_client.post(
                '/api/v1/friends/requests', json={'user_id': masha.id}
            )
        ).json()['id']

        ivan_relation = await ivan_client.get(f'/api/v1/friends/relation/{masha.id}')
        masha_relation = await masha_client.get(f'/api/v1/friends/relation/{ivan.id}')
        assert ivan_relation.status_code == 200
        assert masha_relation.status_code == 200

        assert ivan_relation.json()['is_outgoing_request'] is True
        assert ivan_relation.json()['friendship_id'] == request_id
        assert masha_relation.json()['is_incoming_request'] is True
        assert masha_relation.json()['friendship_id'] == request_id

        await masha_client.post(f'/api/v1/friends/requests/{request_id}/accept')

        accepted = await ivan_client.get(f'/api/v1/friends/relation/{masha.id}')
        assert accepted.json()['is_friend'] is True
        assert accepted.json()['status'] == 'accepted'

    async def test_relation_with_self_returns_400(
        self, ivan_client: AsyncClient, pair
    ) -> None:
        """Связь с самим собой не отдаём."""

        ivan, _ = pair
        response = await ivan_client.get(f'/api/v1/friends/relation/{ivan.id}')
        assert response.status_code == 400

    async def test_relation_with_unknown_user_returns_404(
        self, ivan_client: AsyncClient
    ) -> None:
        """Несуществующий пользователь — 404."""

        response = await ivan_client.get('/api/v1/friends/relation/999999')
        assert response.status_code == 404
