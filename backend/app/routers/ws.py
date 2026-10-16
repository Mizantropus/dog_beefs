"""WebSocket реального времени: подписка на партию + приём команд."""
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter

from .. import realtime, rooms
from ..commands import AnyCommand, CommandError
from ..engine import GameNotFound, engine
from ..store import GameStore, VersionConflict

router = APIRouter()
store = GameStore()


@router.websocket("/ws/games/{game_id}")
async def game_ws(ws: WebSocket, game_id: str, token: str | None = Query(None)):
    await ws.accept()

    try:
        # авторизация: если партия создана из комнаты — проверить токен
        room_exists, seat = await rooms.seat_by_game(game_id, token)
        if room_exists and seat is None:
            await ws.close(code=4403)
            return

        state = await store.load(game_id)
        if state is None:
            await ws.close(code=4404)
            return
    except Exception as e:
        try:
            await ws.send_text(json.dumps({"type": "error", "detail": f"Ошибка подключения: {e}"}, ensure_ascii=False))
            await ws.close(code=1011)
        except Exception:
            pass
        return

    await realtime.register(game_id, ws)
    try:
        # сразу отправить текущий снапшот
        await ws.send_text(realtime.state_message(state))
        while True:
            data = await ws.receive_json()
            if data.get("type") != "command":
                continue
            command = TypeAdapter(AnyCommand).validate_python(data["command"])
            if seat is not None:
                command.seat = seat  # сервер переопределяет seat
            try:
                new_state = await engine.dispatch(game_id, command)
                await realtime.broadcast(game_id, new_state)
            except (CommandError, GameNotFound) as e:
                await ws.send_text(json.dumps({"type": "error", "detail": str(e)}, ensure_ascii=False))
            except VersionConflict:
                await ws.send_text(json.dumps({"type": "error", "detail": "State changed, retry"}, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    finally:
        await realtime.unregister(game_id, ws)