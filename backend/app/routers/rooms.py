"""REST-эндпоинты комнат (лобби): вход по ссылке без аккаунтов."""
from fastapi import APIRouter, Header, HTTPException

from .. import rooms
from ..schemas import (CreateRoomRequest, CreateRoomResponse, JoinRoomRequest,
                       JoinRoomResponse, RoomOut, StartRoomResponse)

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.post("", response_model=CreateRoomResponse, status_code=201)
async def create_room(payload: CreateRoomRequest):
    room = await rooms.create_room(payload.player_count, payload.name)
    return CreateRoomResponse(code=room.code, token=room.host_token, seat=0,
                              player_count=room.player_count)


@router.get("/{code}", response_model=RoomOut)
async def get_room(code: str):
    try:
        room = await rooms.get_room(code)
    except rooms.RoomNotFound:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    return RoomOut(code=room.code, player_count=room.player_count,
                   status=room.status,
                   seats_taken=[t is not None for t in room.seats],
                   names=room.names or [],
                   game_id=room.game_id)


@router.post("/{code}/join", response_model=JoinRoomResponse)
async def join_room(code: str, payload: JoinRoomRequest):
    try:
        token, seat = await rooms.join_room(code, payload.name)
    except rooms.RoomNotFound:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    except rooms.RoomNotJoinable as e:
        raise HTTPException(status_code=409, detail=str(e))
    return JoinRoomResponse(code=code, token=token, seat=seat)


@router.post("/{code}/start", response_model=StartRoomResponse)
async def start_room(code: str, x_player_token: str | None = Header(None, alias="X-Player-Token")):
    try:
        game_id = await rooms.start_game(code, x_player_token or "")
    except rooms.RoomNotFound:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    except rooms.RoomNotHost:
        raise HTTPException(status_code=403, detail="Только хост может начать игру")
    except rooms.RoomNotFull:
        raise HTTPException(status_code=409, detail="Не все места заняты")
    except rooms.RoomNotJoinable as e:
        raise HTTPException(status_code=409, detail=str(e))
    return StartRoomResponse(game_id=game_id)