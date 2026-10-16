"""Комнаты (лобби): создание, вход, старт, привязка игрока к месту.

Без аккаунтов: хост создаёт комнату (получает код-ссылку и токен), остальные
входят по коду и получают свой токен + место (seat). Старт создаёт партию (Game)
и связывает комнату с game_id. Токен используется для авторизации команд.
"""
import secrets
import string

from sqlalchemy import select

from .db import async_session
from .models import Game, Room


class RoomNotFound(Exception):
    pass


class RoomNotJoinable(Exception):
    pass


class RoomNotHost(Exception):
    pass


class RoomNotFull(Exception):
    pass


def _gen_code(n: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def _gen_token() -> str:
    return secrets.token_urlsafe(24)


def seat_for_token(room: Room, token: str | None) -> int | None:
    """Найти место игрока по токену (None — не найдено)."""
    if not token:
        return None
    for seat, t in enumerate(room.seats or []):
        if t == token:
            return seat
    return None


async def create_room(player_count: int) -> Room:
    token = _gen_token()
    seats = [token] + [None] * (player_count - 1)  # хост сразу занимает seat 0
    for _ in range(20):
        code = _gen_code()
        async with async_session() as session:
            if await session.get(Room, code) is None:
                room = Room(code=code, player_count=player_count, status="waiting",
                            host_token=token, seats=seats)
                session.add(room)
                await session.commit()
                return room
    raise RuntimeError("Не удалось сгенерировать код комнаты")


async def get_room(code: str) -> Room:
    async with async_session() as session:
        room = await session.get(Room, code)
        if room is None:
            raise RoomNotFound(code)
        return room


async def join_room(code: str) -> tuple[str, int]:
    """Занять первое свободное место. Возвращает (token, seat)."""
    async with async_session() as session:
        room = await session.get(Room, code)
        if room is None:
            raise RoomNotFound(code)
        if room.status != "waiting":
            raise RoomNotJoinable("Комната уже играет или завершена")
        seats = list(room.seats)
        for seat, t in enumerate(seats):
            if t is None:
                token = _gen_token()
                seats[seat] = token
                room.seats = seats
                await session.commit()
                return token, seat
        raise RoomNotJoinable("Комната заполнена")


async def room_by_game(game_id: str) -> Room | None:
    async with async_session() as session:
        return (await session.execute(
            select(Room).where(Room.game_id == game_id)
        )).scalar_one_or_none()


async def seat_by_game(game_id: str, token: str | None) -> tuple[bool, int | None]:
    """(комната_существует, seat) в одном запросе — без доступа к отцеплённому объекту."""
    async with async_session() as session:
        room = (await session.execute(
            select(Room).where(Room.game_id == game_id)
        )).scalar_one_or_none()
        if room is None:
            return False, None
        return True, seat_for_token(room, token)


async def start_game(code: str, host_token: str) -> str:
    """Начать партию (только хост, когда все места заняты). Возвращает game_id."""
    from .models import ActionCard, District, EventCard, HexEdge
    from .round import prepare_game

    async with async_session() as session:
        room = await session.get(Room, code)
        if room is None:
            raise RoomNotFound(code)
        if room.host_token != host_token:
            raise RoomNotHost("Только хост может начать игру")
        if room.status != "waiting":
            raise RoomNotJoinable("Комната уже играет или завершена")
        if any(t is None for t in room.seats):
            raise RoomNotFull("Не все места заняты")

        action_cards = (await session.execute(select(ActionCard))).scalars().all()
        event_cards = (await session.execute(select(EventCard))).scalars().all()
        districts = (await session.execute(select(District))).scalars().all()
        hex_edges = (await session.execute(select(HexEdge).order_by(HexEdge.id))).scalars().all()

        state = prepare_game(room.player_count, secrets.randbelow(2**31),
                             action_cards, event_cards, districts, hex_edges)
        session.add(Game(id=state.id, version=state.version, status="active",
                         state=state.model_dump(mode="json")))
        room.game_id = state.id
        room.status = "playing"
        await session.commit()
        return state.id