from sqlalchemy import Select, delete, func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.schemas import RelationBrief
from app.modules.friends.enums import FriendshipStatus
from app.modules.friends.exceptions import (
    AlreadyFriendsError,
    BlockAlreadyExistsError,
    BlockNotFoundError,
    FriendError,
    FriendRequestAlreadySentError,
    FriendRequestDeclinedError,
    FriendRequestNotFoundError,
    FriendshipNotFoundError,
    SelfBlockError,
    SelfFriendshipError,
    TargetUserNotFoundError,
    UserBlockedByMeError,
    UserBlockedError,
)
from app.modules.friends.models import Block, Friendship
from app.modules.friends.schemas import (
    BlockRead,
    FriendRequestRead,
    FriendshipRead,
    RelationRead,
)
from app.modules.users.models import User
from app.modules.users.service import UserService

# Ограничение выдачи глобального поиска пользователей
SEARCH_LIMIT = 20


def canonical_pair(a: int, b: int) -> tuple[int, int]:
    """Возвращает упорядоченную пару id: (меньший, больший)."""

    return (a, b) if a < b else (b, a)


def _loads_relations(stmt: Select) -> Select:
    """Дозагружает обоих участников пары, чтобы не делать ленивых запросов."""

    return stmt.options(
        selectinload(Friendship.user),
        selectinload(Friendship.friend),
    )


class FriendService:
    """Сервис бизнес-логики дружеских связей и чёрного списка.

    Все методы выбрасывают доменные исключения модуля ``friends``
    и не знают ничего про HTTP-коды — трансляцией занимается роутер.
    """

    # ==================================================================
    # 1. ВНУТРЕННИЕ ХЕЛПЕРЫ
    # ==================================================================

    @staticmethod
    async def _get_pair(
        session: AsyncSession, me_id: int, other_id: int
    ) -> Friendship | None:
        """Возвращает запись связи для пары пользователей (если есть)."""

        low_id, high_id = canonical_pair(me_id, other_id)
        stmt = select(Friendship).where(
            Friendship.user_id == low_id,
            Friendship.friend_id == high_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_block(
        session: AsyncSession, blocker_id: int, blocked_id: int
    ) -> Block | None:
        """Возвращает запись блокировки конкретного направления."""

        stmt = select(Block).where(
            Block.blocker_id == blocker_id,
            Block.blocked_id == blocked_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _resolve_target(
        session: AsyncSession,
        me: User,
        username: str | None = None,
        user_id: int | None = None,
        self_error: type[FriendError] = SelfFriendshipError,
    ) -> User:
        """Находит целевого пользователя и выполняет базовые проверки.

        Проверки: существует ли пользователь и не является ли он текущим.
        Тип исключения для «самого себя» задаётся вызывающим кодом.
        """

        if username:
            target = await UserService.get_by_username(session, username)
        else:
            target = await UserService.get_by_id(session, user_id)  # type: ignore[arg-type]

        if target is None:
            raise TargetUserNotFoundError()
        if target.id == me.id:
            raise self_error()
        return target

    @staticmethod
    async def _check_blocks(
        session: AsyncSession, me_id: int, target_id: int
    ) -> None:
        """Проверяет блокировки в обе стороны перед созданием связи."""

        if await FriendService._get_block(session, target_id, me_id):
            # Меня заблокировали — не раскрываем причину напрямую
            raise UserBlockedError()
        if await FriendService._get_block(session, me_id, target_id):
            raise UserBlockedByMeError()

    @staticmethod
    async def _get_by_id_or_fail(
        session: AsyncSession, me_id: int, friendship_id: int
    ) -> Friendship:
        """Возвращает запись связи по id, проверяя причастность пользователя."""

        stmt = _loads_relations(
            select(Friendship).where(
                Friendship.id == friendship_id,
                or_(
                    Friendship.user_id == me_id,
                    Friendship.friend_id == me_id,
                ),
            )
        )
        result = await session.execute(stmt)
        friendship = result.scalar_one_or_none()
        if friendship is None:
            raise FriendRequestNotFoundError()
        return friendship

    # ==================================================================
    # 2. ЗАЯВКИ В ДРУЗЬЯ
    # ==================================================================

    @classmethod
    async def send_request(
        cls,
        session: AsyncSession,
        me: User,
        username: str | None = None,
        user_id: int | None = None,
    ) -> FriendRequestRead:
        """Отправляет заявку в друзья либо принимает встречную.

        Логика:
          - пары нет → создаём PENDING;
          - уже друзья → AlreadyFriendsError;
          - моя заявка висит → FriendRequestAlreadySentError;
          - заявка висит мне → принимаем её (ACCEPTED), это и есть «добавить»;
          - заявка была отклонена → FriendRequestDeclinedError.
        """

        target = await cls._resolve_target(session, me, username, user_id)
        await cls._check_blocks(session, me.id, target.id)

        friendship = await cls._get_pair(session, me.id, target.id)

        if friendship is not None:
            if friendship.status == FriendshipStatus.ACCEPTED:
                raise AlreadyFriendsError()
            if friendship.status == FriendshipStatus.DECLINED:
                raise FriendRequestDeclinedError()
            if friendship.initiator_id == me.id:
                raise FriendRequestAlreadySentError()

            # Встречная заявка — принимаем её
            friendship.status = FriendshipStatus.ACCEPTED
            await session.commit()
            await session.refresh(friendship)
            return cls._to_request_schema(friendship, me.id)

        low_id, high_id = canonical_pair(me.id, target.id)
        friendship = Friendship(
            user_id=low_id,
            friend_id=high_id,
            initiator_id=me.id,
            status=FriendshipStatus.PENDING,
        )
        session.add(friendship)
        await session.commit()
        await session.refresh(friendship)
        return cls._to_request_schema(friendship, me.id)

    @classmethod
    async def accept_request(
        cls, session: AsyncSession, me: User, request_id: int
    ) -> FriendshipRead:
        """Принимает входящую заявку."""

        friendship = await cls._get_by_id_or_fail(session, me.id, request_id)

        if friendship.status == FriendshipStatus.ACCEPTED:
            raise AlreadyFriendsError()
        if friendship.status == FriendshipStatus.DECLINED:
            raise FriendRequestDeclinedError()
        if friendship.initiator_id == me.id:
            # Нельзя принять собственную заявку
            raise FriendRequestNotFoundError()

        await cls._check_blocks(session, me.id, friendship.partner_id(me.id))

        friendship.status = FriendshipStatus.ACCEPTED
        await session.commit()
        await session.refresh(friendship)
        return cls._to_schema(friendship, me.id)

    @classmethod
    async def decline_request(
        cls, session: AsyncSession, me: User, request_id: int
    ) -> None:
        """Отклоняет входящую заявку: запись остаётся со статусом DECLINED."""

        friendship = await cls._get_by_id_or_fail(session, me.id, request_id)

        if friendship.status != FriendshipStatus.PENDING:
            raise FriendRequestNotFoundError()
        if friendship.initiator_id == me.id:
            raise FriendRequestNotFoundError()

        friendship.status = FriendshipStatus.DECLINED
        await session.commit()

    @classmethod
    async def cancel_request(
        cls, session: AsyncSession, me: User, request_id: int
    ) -> None:
        """Отзывает собственную исходящую заявку (удаляет запись)."""

        friendship = await cls._get_by_id_or_fail(session, me.id, request_id)

        if (
            friendship.status != FriendshipStatus.PENDING
            or friendship.initiator_id != me.id
        ):
            raise FriendRequestNotFoundError()

        await session.delete(friendship)
        await session.commit()

    @classmethod
    async def remove_friend(
        cls, session: AsyncSession, me: User, friend_id: int
    ) -> None:
        """Удаляет пользователя из друзей."""

        friendship = await cls._get_pair(session, me.id, friend_id)

        if friendship is None or friendship.status != FriendshipStatus.ACCEPTED:
            raise FriendshipNotFoundError()

        await session.delete(friendship)
        await session.commit()

    # ==================================================================
    # 3. СПИСКИ
    # ==================================================================

    @classmethod
    async def list_by_status(
        cls,
        session: AsyncSession,
        me: User,
        status: FriendshipStatus,
        initiated_by_me: bool | None = None,
    ) -> list[FriendshipRead]:
        """Общий метод выборки связей по статусу и направлению."""

        conditions = [
            or_(Friendship.user_id == me.id, Friendship.friend_id == me.id),
            Friendship.status == status,
        ]
        if initiated_by_me is True:
            conditions.append(Friendship.initiator_id == me.id)
        elif initiated_by_me is False:
            conditions.append(Friendship.initiator_id != me.id)

        stmt = _loads_relations(
            select(Friendship)
            .where(*conditions)
            .order_by(Friendship.created_at.desc())
        )
        result = await session.execute(stmt)
        return [cls._to_schema(item, me.id) for item in result.scalars().all()]

    @classmethod
    async def list_friends(
        cls, session: AsyncSession, me: User
    ) -> list[FriendshipRead]:
        """Список друзей текущего пользователя."""

        return await cls.list_by_status(session, me, FriendshipStatus.ACCEPTED)

    @classmethod
    async def list_incoming(
        cls, session: AsyncSession, me: User
    ) -> list[FriendRequestRead]:
        """Входящие заявки (жду ответа от меня)."""

        return await cls.list_by_status(
            session, me, FriendshipStatus.PENDING, initiated_by_me=False
        )

    @classmethod
    async def list_outgoing(
        cls, session: AsyncSession, me: User
    ) -> list[FriendRequestRead]:
        """Исходящие заявки (жду ответа от собеседника)."""

        return await cls.list_by_status(
            session, me, FriendshipStatus.PENDING, initiated_by_me=True
        )

    @classmethod
    async def is_friend(
        cls, session: AsyncSession, me_id: int, other_id: int
    ) -> bool:
        """Проверка, являются ли пользователи друзьями (для других модулей)."""

        friendship = await cls._get_pair(session, me_id, other_id)
        return bool(friendship and friendship.status == FriendshipStatus.ACCEPTED)

    # ==================================================================
    # 4. ЧЁРНЫЙ СПИСОК
    # ==================================================================

    @classmethod
    async def block_user(
        cls,
        session: AsyncSession,
        me: User,
        username: str | None = None,
        user_id: int | None = None,
    ) -> BlockRead:
        """Блокирует пользователя и разрывает существующую связь с ним."""

        target = await cls._resolve_target(
            session, me, username, user_id, self_error=SelfBlockError
        )

        if await cls._get_block(session, me.id, target.id):
            raise BlockAlreadyExistsError()

        # Блокировка разрывает дружбу и удаляет любые заявки между парой
        friendship = await cls._get_pair(session, me.id, target.id)
        if friendship is not None:
            await session.delete(friendship)

        block = Block(blocker_id=me.id, blocked_id=target.id)
        session.add(block)
        await session.commit()

        stmt = (
            select(Block)
            .where(Block.id == block.id)
            .options(selectinload(Block.blocked))
        )
        result = await session.execute(stmt)
        return BlockRead.model_validate(result.scalar_one())

    @classmethod
    async def unblock_user(
        cls, session: AsyncSession, me: User, blocked_id: int
    ) -> None:
        """Убирает пользователя из чёрного списка."""

        block = await cls._get_block(session, me.id, blocked_id)
        if block is None:
            raise BlockNotFoundError()

        await session.delete(block)
        await session.commit()

    @staticmethod
    async def list_blocks(session: AsyncSession, me: User) -> list[BlockRead]:
        """Чёрный список текущего пользователя."""

        stmt = (
            select(Block)
            .where(Block.blocker_id == me.id)
            .options(selectinload(Block.blocked))
            .order_by(Block.created_at.desc())
        )
        result = await session.execute(stmt)
        return [BlockRead.model_validate(item) for item in result.scalars().all()]

    # ==================================================================
    # 5. СОСТОЯНИЕ СВЯЗИ И ПОИСК
    # ==================================================================

    @classmethod
    async def get_relation(
        cls, session: AsyncSession, me: User, target_id: int
    ) -> RelationRead:
        """Возвращает сводное состояние связи с указанным пользователем."""

        if target_id == me.id:
            raise SelfFriendshipError()

        target = await UserService.get_by_id(session, target_id)
        if target is None:
            raise TargetUserNotFoundError()

        friendship = await cls._get_pair(session, me.id, target_id)
        blocked_by_me = await cls._get_block(session, me.id, target_id)
        blocked_me = await cls._get_block(session, target_id, me.id)

        relation = RelationRead(
            user_id=target_id,
            status=friendship.status if friendship else None,
            friendship_id=friendship.id if friendship else None,
            is_blocked_by_me=blocked_by_me is not None,
            is_blocked_me=blocked_me is not None,
        )

        if friendship is not None:
            relation.is_friend = friendship.status == FriendshipStatus.ACCEPTED
            relation.is_declined = friendship.status == FriendshipStatus.DECLINED
            if friendship.status == FriendshipStatus.PENDING:
                if friendship.initiator_id == me.id:
                    relation.is_outgoing_request = True
                else:
                    relation.is_incoming_request = True

        return relation

    @classmethod
    async def bulk_relations(
        cls, session: AsyncSession, me_id: int, target_ids: list[int]
    ) -> dict[int, RelationBrief]:
        """Возвращает состояние связи сразу с несколькими пользователями.

        Два запроса на всю выдачу вместо N+1 по одному на пользователя —
        используется в результатах поиска.
        """

        if not target_ids:
            return {}

        pairs = [canonical_pair(me_id, target_id) for target_id in target_ids]

        friendship_stmt = select(Friendship).where(
            tuple_(Friendship.user_id, Friendship.friend_id).in_(pairs)
        )
        block_stmt = select(Block).where(
            Block.blocker_id == me_id,
            Block.blocked_id.in_(target_ids),
        )
        blocked_me_stmt = select(Block).where(
            Block.blocked_id == me_id,
            Block.blocker_id.in_(target_ids),
        )

        friendships = (await session.execute(friendship_stmt)).scalars().all()
        blocked_by_me = {b.blocked_id for b in (await session.execute(block_stmt)).scalars()}
        blocked_me = {b.blocker_id for b in (await session.execute(blocked_me_stmt)).scalars()}

        by_pair = {(f.user_id, f.friend_id): f for f in friendships}

        relations: dict[int, RelationBrief] = {}
        for target_id in target_ids:
            friendship = by_pair.get(canonical_pair(me_id, target_id))
            relation = RelationBrief(
                is_blocked_by_me=target_id in blocked_by_me,
                is_blocked_me=target_id in blocked_me,
            )
            if friendship is not None:
                relation.status = friendship.status
                relation.friendship_id = friendship.id
                relation.is_friend = friendship.status == FriendshipStatus.ACCEPTED
                relation.is_declined = friendship.status == FriendshipStatus.DECLINED
                if friendship.status == FriendshipStatus.PENDING:
                    if friendship.initiator_id == me_id:
                        relation.is_outgoing_request = True
                    else:
                        relation.is_incoming_request = True
            relations[target_id] = relation
        return relations

    @staticmethod
    async def search_users(
        session: AsyncSession, me: User, query: str
    ) -> list[User]:
        """Глобальный поиск пользователей по username или имени.

        Возвращает ORM-объекты: фильтрацию полей по настройкам приватности
        выполняет вызывающий код (``UserService.search``).
        """

        pattern = f'%{query.strip()}%'
        stmt = (
            select(User)
            .where(
                User.id != me.id,
                User.is_active.is_(True),
                or_(
                    User.username.ilike(pattern),
                    User.first_name.ilike(pattern),
                ),
            )
            .order_by(User.username)
            .limit(SEARCH_LIMIT)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_friends(session: AsyncSession, me_id: int) -> int:
        """Количество друзей (для бейджей в интерфейсе)."""

        stmt = select(func.count(Friendship.id)).where(
            Friendship.status == FriendshipStatus.ACCEPTED,
            or_(Friendship.user_id == me_id, Friendship.friend_id == me_id),
        )
        result = await session.execute(stmt)
        return int(result.scalar_one())

    # ==================================================================
    # 6. СЕРИАЛИЗАЦИЯ
    # ==================================================================

    @staticmethod
    def _to_schema(friendship: Friendship, me_id: int) -> FriendshipRead:
        """Собирает схему связи с подстановкой «второго» пользователя."""

        data = FriendshipRead.model_validate(friendship)
        return data.with_perspective(me_id)

    @staticmethod
    def _to_request_schema(friendship: Friendship, me_id: int) -> FriendRequestRead:
        """Собирает схему заявки с подстановкой «второго» пользователя."""

        data = FriendRequestRead.model_validate(friendship)
        return data.with_perspective(me_id)


async def purge_pair(session: AsyncSession, me_id: int, other_id: int) -> None:
    """Полностью удаляет любую запись связи между парой пользователей."""

    low_id, high_id = canonical_pair(me_id, other_id)
    await session.execute(
        delete(Friendship).where(
            Friendship.user_id == low_id,
            Friendship.friend_id == high_id,
        )
    )
