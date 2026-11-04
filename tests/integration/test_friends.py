"""Интеграционные тесты модуля друзей: заявки, чёрный список, поиск.

Тесты работают через реальные HTTP-вызовы и реального текущего пользователя,
чтобы проверить каноническое хранение пары ``user_id < friend_id`` и
корректную подстановку ``other_user`` для обеих сторон связи.
"""

from typing import Any

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user
from app.main import app
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService

FRIENDS = '/api/v1/friends'
SEARCH = '/api/v1/users/search'


# ==============================================================================
# ФИКСТУРЫ И ОБЁРТКА НАД КЛИЕНТОМ
# ==============================================================================
@pytest.fixture
async def ivan_and_masha(db, user_data_factory) -> tuple[User, User]:
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


class Actor:
    """Клиент, привязанный к конкретному пользователю.

    Перед каждым запросом подменяет зависимость ``get_current_user``, поэтому
    в одном тесте можно свободно ходить то за одну, то за другую сторону.
    """

    def __init__(self, client: AsyncClient, user: User) -> None:
        self._client = client
        self.user = user

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def username(self) -> str:
        return self.user.username

    def _impersonate(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: self.user

    async def request(self, method: str, url: str, **kwargs: Any):
        self._impersonate()
        return await self._client.request(method, url, **kwargs)

    async def get(self, url: str, **kwargs: Any):
        return await self.request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs: Any):
        return await self.request('POST', url, **kwargs)

    async def delete(self, url: str, **kwargs: Any):
        return await self.request('DELETE', url, **kwargs)

    # --- короткие хелперы предметной области ---
    async def send_request(self, target: 'Actor'):
        return await self.post(f'{FRIENDS}/requests', json={'user_id': target.id})

    async def accept(self, request_id: int):
        return await self.post(f'{FRIENDS}/requests/{request_id}/accept')

    async def decline(self, request_id: int):
        return await self.post(f'{FRIENDS}/requests/{request_id}/decline')

    async def cancel(self, request_id: int):
        return await self.delete(f'{FRIENDS}/requests/{request_id}')

    async def friends(self):
        return await self.get(FRIENDS)

    async def incoming(self):
        return await self.get(f'{FRIENDS}/requests/incoming')

    async def outgoing(self):
        return await self.get(f'{FRIENDS}/requests/outgoing')

    async def blocks(self):
        return await self.get(f'{FRIENDS}/blocks')

    async def block(self, target_id: int):
        return await self.post(f'{FRIENDS}/blocks', json={'user_id': target_id})

    async def unblock(self, target_id: int):
        return await self.delete(f'{FRIENDS}/blocks/{target_id}')

    async def relation(self, target_id: int):
        return await self.get(f'{FRIENDS}/relation/{target_id}')

    async def patch_profile(self, payload: dict):
        return await self.request('PATCH', '/api/v1/users/me', json=payload)


@pytest.fixture
async def ivan(client: AsyncClient, ivan_and_masha) -> Actor:
    return Actor(client, ivan_and_masha[0])


@pytest.fixture
async def masha(client: AsyncClient, ivan_and_masha) -> Actor:
    return Actor(client, ivan_and_masha[1])


@pytest.fixture(autouse=True)
def _clear_overrides():
    """Убирает подмену авторизации после каждого теста."""

    yield
    app.dependency_overrides.pop(get_current_user, None)


async def make_request(ivan: Actor, masha: Actor) -> int:
    """Создаёт заявку Иван → Маша и возвращает её id."""

    response = await ivan.send_request(masha)
    assert response.status_code == 201, response.text
    return response.json()['id']


async def make_friends(ivan: Actor, masha: Actor) -> int:
    """Создаёт и принимает заявку Иван → Маша."""

    request_id = await make_request(ivan, masha)
    accepted = await masha.accept(request_id)
    assert accepted.status_code == 200, accepted.text
    return request_id


# ==============================================================================
# 1. ОТПРАВКА ЗАЯВКИ
# ==============================================================================
class TestSendRequest:
    """POST /api/v1/friends/requests"""

    async def test_success_returns_201_and_pair_is_canonical(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Заявка создаётся, пара хранится в каноническом виде."""

        response = await ivan.send_request(masha)

        assert response.status_code == 201
        data = response.json()
        assert data['status'] == 'pending'
        assert data['initiator_id'] == ivan.id
        assert data['initiated_by_me'] is True
        assert data['other_user']['username'] == masha.username
        # Канонический порядок: user_id всегда меньше friend_id
        assert data['user']['id'] == min(ivan.id, masha.id)
        assert data['friend']['id'] == max(ivan.id, masha.id)

    async def test_by_username(self, ivan: Actor, masha: Actor) -> None:
        """Заявку можно отправить по username."""

        response = await ivan.post(
            f'{FRIENDS}/requests', json={'username': masha.username}
        )

        assert response.status_code == 201
        assert response.json()['other_user']['id'] == masha.id

    async def test_requires_exactly_one_identifier(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Без идентификатора или с обоими сразу — 422."""

        empty = await ivan.post(f'{FRIENDS}/requests', json={})
        assert empty.status_code == 422

        both = await ivan.post(
            f'{FRIENDS}/requests',
            json={'username': masha.username, 'user_id': masha.id},
        )
        assert both.status_code == 422

    async def test_self_request_returns_400(self, ivan: Actor) -> None:
        """Нельзя добавить в друзья самого себя."""

        response = await ivan.post(f'{FRIENDS}/requests', json={'user_id': ivan.id})

        assert response.status_code == 400
        assert 'самого себя' in response.json()['detail']

    async def test_unknown_user_returns_404(self, ivan: Actor) -> None:
        """Несуществующий пользователь — 404."""

        response = await ivan.post(f'{FRIENDS}/requests', json={'user_id': 999999})

        assert response.status_code == 404

    async def test_duplicate_request_returns_400(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Повторная отправка той же заявки — 400."""

        assert (await ivan.send_request(masha)).status_code == 201

        second = await ivan.send_request(masha)
        assert second.status_code == 400
        assert 'уже отправлена' in second.json()['detail']

    async def test_counter_request_auto_accepts(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Встречная заявка принимается автоматически."""

        assert (await ivan.send_request(masha)).status_code == 201

        counter = await masha.send_request(ivan)
        assert counter.status_code == 201
        assert counter.json()['status'] == 'accepted'

        friends = await ivan.friends()
        assert friends.status_code == 200
        assert len(friends.json()) == 1

    async def test_unauthorized_returns_401(self, client: AsyncClient) -> None:
        """Без токена список друзей недоступен."""

        app.dependency_overrides.pop(get_current_user, None)
        response = await client.get(FRIENDS)

        assert response.status_code == 401


# ==============================================================================
# 2. СПИСКИ
# ==============================================================================
class TestLists:
    """Списки друзей, входящих и исходящих заявок."""

    async def test_incoming_and_outgoing_are_perspective_aware(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """У каждой стороны свой список и свой other_user."""

        await ivan.send_request(masha)

        ivan_outgoing = await ivan.outgoing()
        ivan_incoming = await ivan.incoming()
        masha_incoming = await masha.incoming()
        masha_outgoing = await masha.outgoing()

        assert len(ivan_outgoing.json()) == 1
        assert ivan_outgoing.json()[0]['other_user']['id'] == masha.id
        assert ivan_outgoing.json()[0]['initiated_by_me'] is True
        assert ivan_incoming.json() == []

        assert len(masha_incoming.json()) == 1
        assert masha_incoming.json()[0]['other_user']['id'] == ivan.id
        assert masha_incoming.json()[0]['initiated_by_me'] is False
        assert masha_outgoing.json() == []

        # До принятия список друзей пуст у обоих
        assert (await ivan.friends()).json() == []
        assert (await masha.friends()).json() == []

    async def test_friends_list_after_accept(self, ivan: Actor, masha: Actor) -> None:
        """После принятия оба видят друг друга в друзьях."""

        await make_friends(ivan, masha)

        for actor, other in ((ivan, masha), (masha, ivan)):
            friends = await actor.friends()
            assert friends.status_code == 200
            body = friends.json()
            assert len(body) == 1
            assert body[0]['other_user']['username'] == other.username
            assert body[0]['status'] == 'accepted'


# ==============================================================================
# 3. ПРИНЯТИЕ / ОТКЛОНЕНИЕ / ОТЗЫВ / УДАЛЕНИЕ
# ==============================================================================
class TestRequestActions:
    """Действия над заявками и дружбой."""

    async def test_accept_own_request_returns_404(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Собственную заявку принять нельзя."""

        request_id = await make_request(ivan, masha)

        response = await ivan.accept(request_id)
        assert response.status_code == 404

    async def test_decline_blocks_resend(self, ivan: Actor, masha: Actor) -> None:
        """Отклонённую заявку нельзя отправить повторно."""

        request_id = await make_request(ivan, masha)

        assert (await masha.decline(request_id)).status_code == 204
        assert (await masha.incoming()).json() == []

        again = await ivan.send_request(masha)
        assert again.status_code == 400
        assert 'отклонена' in again.json()['detail']

        relation = await ivan.relation(masha.id)
        assert relation.json()['is_declined'] is True
        assert relation.json()['is_friend'] is False

    async def test_cancel_outgoing_request(self, ivan: Actor, masha: Actor) -> None:
        """Инициатор может отозвать свою заявку и отправить заново."""

        request_id = await make_request(ivan, masha)

        assert (await ivan.cancel(request_id)).status_code == 204
        assert (await ivan.outgoing()).json() == []
        assert (await masha.incoming()).json() == []

        assert (await ivan.send_request(masha)).status_code == 201

    async def test_remove_friend(self, ivan: Actor, masha: Actor) -> None:
        """Удаление из друзей разрывает связь у обеих сторон."""

        await make_friends(ivan, masha)

        assert (await ivan.delete(f'{FRIENDS}/{masha.id}')).status_code == 204
        assert (await ivan.friends()).json() == []
        assert (await masha.friends()).json() == []

        second = await ivan.delete(f'{FRIENDS}/{masha.id}')
        assert second.status_code == 404

    async def test_remove_stranger_returns_404(self, ivan: Actor, masha: Actor) -> None:
        """Удалить не-друга нельзя."""

        response = await ivan.delete(f'{FRIENDS}/{masha.id}')
        assert response.status_code == 404


# ==============================================================================
# 4. ЧЁРНЫЙ СПИСОК
# ==============================================================================
class TestBlocks:
    """Блокировки и их влияние на заявки."""

    async def test_block_breaks_friendship(self, ivan: Actor, masha: Actor) -> None:
        """Блокировка удаляет существующую дружбу."""

        await make_friends(ivan, masha)

        blocked = await ivan.block(masha.id)
        assert blocked.status_code == 201
        assert blocked.json()['blocked']['id'] == masha.id

        assert (await ivan.friends()).json() == []
        assert (await masha.friends()).json() == []
        assert len((await ivan.blocks()).json()) == 1

    async def test_blocked_user_cannot_send_request(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Заблокированный получает 404 — факт блокировки не раскрываем."""

        await ivan.block(masha.id)

        response = await masha.send_request(ivan)
        assert response.status_code == 404

    async def test_request_to_blocked_user_returns_400(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Нельзя отправить заявку тому, кого сам заблокировал."""

        await ivan.block(masha.id)

        response = await ivan.send_request(masha)
        assert response.status_code == 400
        assert 'разблокируйте' in response.json()['detail'].lower()

    async def test_accept_after_block_returns_404(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Блокировка удаляет и зависшую заявку — принимать нечего."""

        request_id = await make_request(ivan, masha)
        await ivan.block(masha.id)

        assert (await masha.accept(request_id)).status_code == 404

    async def test_duplicate_block_and_unblock(self, ivan: Actor, masha: Actor) -> None:
        """Повторный блок — 400, разблокировка — 204, повторная — 404."""

        assert (await ivan.block(masha.id)).status_code == 201
        assert (await ivan.block(masha.id)).status_code == 400

        assert (await ivan.unblock(masha.id)).status_code == 204
        assert (await ivan.blocks()).json() == []
        assert (await ivan.unblock(masha.id)).status_code == 404

    async def test_block_self_returns_400(self, ivan: Actor) -> None:
        """Заблокировать себя нельзя."""

        response = await ivan.block(ivan.id)
        assert response.status_code == 400


# ==============================================================================
# 5. ПОИСК И СОСТОЯНИЕ СВЯЗИ
# ==============================================================================
class TestSearchAndRelation:
    """GET /api/v1/users/search и GET /api/v1/friends/relation/{id}"""

    async def test_search_finds_by_username_with_relation(
        self, ivan: Actor, masha: Actor
    ) -> None:
        """Поиск находит пользователя и отдаёт состояние связи."""

        response = await ivan.get(SEARCH, params={'q': 'masha'})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]['username'] == masha.username
        assert body[0]['relation'] is not None
        assert body[0]['relation']['is_friend'] is False

        await ivan.send_request(masha)

        second = await ivan.get(SEARCH, params={'q': 'masha'})
        relation = second.json()[0]['relation']
        assert relation['is_outgoing_request'] is True
        assert relation['status'] == 'pending'

    async def test_search_finds_by_first_name(self, ivan: Actor) -> None:
        """Поиск работает и по имени."""

        response = await ivan.get(SEARCH, params={'q': 'Маш'})
        assert response.status_code == 200
        assert [item['username'] for item in response.json()] == ['masha_95']

    async def test_search_does_not_return_self(self, ivan: Actor) -> None:
        """Себя в выдаче нет."""

        response = await ivan.get(SEARCH, params={'q': 'ivan'})
        assert response.status_code == 200
        assert all(item['id'] != ivan.id for item in response.json())

    async def test_search_requires_min_length(self, ivan: Actor) -> None:
        """Запрос короче двух символов — 422."""

        response = await ivan.get(SEARCH, params={'q': 'a'})
        assert response.status_code == 422

    async def test_search_respects_privacy(self, ivan: Actor, masha: Actor) -> None:
        """Скрытый приватностью город не попадает в выдачу поиска."""

        await masha.patch_profile({'city': 'Томск', 'privacy_settings': {'show_city': False}})

        response = await ivan.get(SEARCH, params={'q': 'masha'})
        assert response.json()[0]['city'] is None

    async def test_relation_endpoint(self, ivan: Actor, masha: Actor) -> None:
        """Сводка состояния связи для обеих сторон."""

        request_id = await make_request(ivan, masha)

        ivan_relation = await ivan.relation(masha.id)
        masha_relation = await masha.relation(ivan.id)
        assert ivan_relation.status_code == 200
        assert masha_relation.status_code == 200

        assert ivan_relation.json()['is_outgoing_request'] is True
        assert ivan_relation.json()['friendship_id'] == request_id
        assert masha_relation.json()['is_incoming_request'] is True
        assert masha_relation.json()['friendship_id'] == request_id

        await masha.accept(request_id)

        accepted = await ivan.relation(masha.id)
        assert accepted.json()['is_friend'] is True
        assert accepted.json()['status'] == 'accepted'

    async def test_relation_with_self_returns_400(self, ivan: Actor) -> None:
        """Связь с самим собой не отдаём."""

        response = await ivan.relation(ivan.id)
        assert response.status_code == 400

    async def test_relation_with_unknown_user_returns_404(self, ivan: Actor) -> None:
        """Несуществующий пользователь — 404."""

        response = await ivan.relation(999999)
        assert response.status_code == 404
