"""REST-эндпоинты партий: создание, загрузка снапшота, команды."""
import secrets

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select

from .. import realtime, rooms
from ..commands import AnyCommand, CommandError
from ..db import async_session
from ..engine import GameNotFound, engine
from ..models import ActionCard, District, EventCard, HexEdge, Move
from ..round import prepare_game
from ..schemas import CreateGameRequest, MoveOut
from ..state import GameState
from ..store import GameStore, VersionConflict

router = APIRouter(prefix="/api/games", tags=["games"])
store = GameStore()


@router.post("", response_model=GameState)
async def create_game(payload: CreateGameRequest):
    async with async_session() as session:
        action_cards = (await session.execute(select(ActionCard))).scalars().all()
        event_cards = (await session.execute(select(EventCard))).scalars().all()
        districts = (await session.execute(select(District))).scalars().all()
        hex_edges = (await session.execute(select(HexEdge).order_by(HexEdge.id))).scalars().all()
    seed = payload.seed if payload.seed is not None else secrets.randbelow(2**31)
    state = prepare_game(payload.player_count, seed, action_cards, event_cards, districts, hex_edges)
    await store.create(state)
    return state


@router.get("/{game_id}", response_model=GameState)
async def get_game(game_id: str):
    state = await store.load(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return state


@router.post("/{game_id}/commands", response_model=GameState)
async def post_command(game_id: str, command: AnyCommand,
                       x_player_token: str | None = Header(None, alias="X-Player-Token")):
    # Авторизация: если партия создана из комнаты — требовать токен игрока.
    room = await rooms.room_by_game(game_id)
    if room is not None:
        seat = rooms.seat_for_token(room, x_player_token)
        if seat is None:
            raise HTTPException(status_code=403, detail="Не авторизован: нет токена или места")
        command.seat = seat  # сервер переопределяет seat — защита от подмены
    try:
        new_state = await engine.dispatch(game_id, command)
        await realtime.broadcast(game_id, new_state)
        return new_state
    except GameNotFound:
        raise HTTPException(status_code=404, detail="Game not found")
    except CommandError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except VersionConflict:
        raise HTTPException(status_code=409, detail="State changed, retry")

@router.get("/{game_id}/moves", response_model=list[MoveOut])
async def list_moves(game_id: str, since: int = 0):
    """Журнал ходов партии (с версии > since) — для реплея/зрителей."""
    async with async_session() as session:
        rows = await session.execute(
            select(Move).where(Move.game_id == game_id, Move.version > since).order_by(Move.id)
        )
        return rows.scalars().all()
