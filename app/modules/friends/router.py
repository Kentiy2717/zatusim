from typing import Annotated

from fastapi import APIRouter, Path, Response, status
from fastapi.exceptions import HTTPException

from app.api.deps import CurrentUser, DbSession
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
from app.modules.friends.schemas import (
    BlockCreate,
    BlockRead,
    FriendRequestCreate,
    FriendRequestRead,
    FriendshipRead,
    RelationRead,
)
from app.modules.friends.service import FriendService

router = APIRouter(prefix='/friends', tags=['Friends'])

# Соответствие доменных исключений модуля HTTP-кодам
_FRIEND_EXCEPTION_STATUS: dict[type[FriendError], int] = {
    TargetUserNotFoundError: status.HTTP_404_NOT_FOUND,
    FriendRequestNotFoundError: status.HTTP_404_NOT_FOUND,
    FriendshipNotFoundError: status.HTTP_404_NOT_FOUND,
    BlockNotFoundError: status.HTTP_404_NOT_FOUND,
    # Факт блокировки не раскрываем — выглядело бы как утечка данных
    UserBlockedError: status.HTTP_404_NOT_FOUND,
    SelfFriendshipError: status.HTTP_400_BAD_REQUEST,
    SelfBlockError: status.HTTP_400_BAD_REQUEST,
    AlreadyFriendsError: status.HTTP_400_BAD_REQUEST,
    FriendRequestAlreadySentError: status.HTTP_400_BAD_REQUEST,
    FriendRequestDeclinedError: status.HTTP_400_BAD_REQUEST,
    UserBlockedByMeError: status.HTTP_400_BAD_REQUEST,
    BlockAlreadyExistsError: status.HTTP_400_BAD_REQUEST,
}


def _to_http_exception(exc: FriendError) -> HTTPException:
    """Транслирует доменное исключение модуля в HTTPException."""

    return HTTPException(
        status_code=_FRIEND_EXCEPTION_STATUS.get(
            type(exc), status.HTTP_400_BAD_REQUEST
        ),
        detail=exc.message,
    )


# ======================================================================
# 1. ЧЁРНЫЙ СПИСОК
# ======================================================================
@router.get(
    '/blocks',
    response_model=list[BlockRead],
    summary='Мой чёрный список',
)
async def list_blocks(
    session: DbSession,
    current_user: CurrentUser,
) -> list[BlockRead]:
    """Возвращает список заблокированных мной пользователей."""

    return await FriendService.list_blocks(session, current_user)


@router.post(
    '/blocks',
    response_model=BlockRead,
    status_code=status.HTTP_201_CREATED,
    summary='Заблокировать пользователя',
)
async def block_user(
    data: BlockCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> BlockRead:
    """Блокирует пользователя и разрывает существующую связь/заявки с ним."""

    try:
        return await FriendService.block_user(
            session=session,
            me=current_user,
            username=data.username,
            user_id=data.user_id,
        )
    except FriendError as exc:
        raise _to_http_exception(exc) from exc


@router.delete(
    '/blocks/{blocked_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Разблокировать пользователя',
)
async def unblock_user(
    session: DbSession,
    current_user: CurrentUser,
    blocked_id: Annotated[int, Path(description='ID разблокируемого пользователя')],
) -> Response:
    """Удаляет запись из чёрного списка."""

    try:
        await FriendService.unblock_user(session, current_user, blocked_id)
    except FriendError as exc:
        raise _to_http_exception(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ======================================================================
# 2. СОСТОЯНИЕ СВЯЗИ
# ======================================================================
@router.get(
    '/relation/{user_id}',
    response_model=RelationRead,
    summary='Состояние связи с пользователем',
)
async def get_relation(
    session: DbSession,
    current_user: CurrentUser,
    user_id: Annotated[int, Path(description='ID проверяемого пользователя')],
) -> RelationRead:
    """Возвращает сводку: друзья / заявка / отклонено / заблокирован.

    Используется клиентом для выбора кнопки на карточке пользователя.
    """

    try:
        return await FriendService.get_relation(session, current_user, user_id)
    except FriendError as exc:
        raise _to_http_exception(exc) from exc


# ======================================================================
# 3. СПИСКИ ДРУЗЕЙ И ЗАЯВОК
# ======================================================================
@router.get(
    '',
    response_model=list[FriendshipRead],
    summary='Мои друзья',
)
async def list_friends(
    session: DbSession,
    current_user: CurrentUser,
) -> list[FriendshipRead]:
    """Возвращает принятые дружеские связи текущего пользователя."""

    return await FriendService.list_friends(session, current_user)


@router.get(
    '/requests/incoming',
    response_model=list[FriendRequestRead],
    summary='Входящие заявки в друзья',
)
async def list_incoming_requests(
    session: DbSession,
    current_user: CurrentUser,
) -> list[FriendRequestRead]:
    """Заявки, которые ожидают моего ответа."""

    return await FriendService.list_incoming(session, current_user)


@router.get(
    '/requests/outgoing',
    response_model=list[FriendRequestRead],
    summary='Исходящие заявки в друзья',
)
async def list_outgoing_requests(
    session: DbSession,
    current_user: CurrentUser,
) -> list[FriendRequestRead]:
    """Мои заявки, ожидающие ответа собеседника."""

    return await FriendService.list_outgoing(session, current_user)


@router.post(
    '/requests',
    response_model=FriendRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary='Отправить заявку в друзья',
)
async def send_friend_request(
    data: FriendRequestCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> FriendRequestRead:
    """Отправляет заявку, а при наличии встречной — сразу принимает её."""

    try:
        return await FriendService.send_request(
            session=session,
            me=current_user,
            username=data.username,
            user_id=data.user_id,
        )
    except FriendError as exc:
        raise _to_http_exception(exc) from exc


@router.post(
    '/requests/{request_id}/accept',
    response_model=FriendshipRead,
    summary='Принять заявку в друзья',
)
async def accept_friend_request(
    session: DbSession,
    current_user: CurrentUser,
    request_id: Annotated[int, Path(description='ID записи связи (friendship id)')],
) -> FriendshipRead:
    """Переводит входящую заявку в статус ACCEPTED."""

    try:
        return await FriendService.accept_request(session, current_user, request_id)
    except FriendError as exc:
        raise _to_http_exception(exc) from exc


@router.post(
    '/requests/{request_id}/decline',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Отклонить заявку в друзья',
)
async def decline_friend_request(
    session: DbSession,
    current_user: CurrentUser,
    request_id: Annotated[int, Path(description='ID записи связи (friendship id)')],
) -> Response:
    """Переводит входящую заявку в статус DECLINED (повторная отправка запрещена)."""

    try:
        await FriendService.decline_request(session, current_user, request_id)
    except FriendError as exc:
        raise _to_http_exception(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    '/requests/{request_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Отозвать свою заявку',
)
async def cancel_friend_request(
    session: DbSession,
    current_user: CurrentUser,
    request_id: Annotated[int, Path(description='ID записи связи (friendship id)')],
) -> Response:
    """Удаляет мою исходящую заявку, ожидающую ответа."""

    try:
        await FriendService.cancel_request(session, current_user, request_id)
    except FriendError as exc:
        raise _to_http_exception(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    '/{friend_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Удалить из друзей',
)
async def remove_friend(
    session: DbSession,
    current_user: CurrentUser,
    friend_id: Annotated[int, Path(description='ID удаляемого друга')],
) -> Response:
    """Разрывает принятую дружескую связь."""

    try:
        await FriendService.remove_friend(session, current_user, friend_id)
    except FriendError as exc:
        raise _to_http_exception(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
