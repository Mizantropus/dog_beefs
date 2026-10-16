"""Реальное время: рассылка снапшотов игрокам.

Внутри процесса — набор WebSocket-соединений по game_id.
Redis (если задан REDIS_URL) — pub/sub для распространения между экземплярами:
`broadcast` публикует в канал `game:{id}`, фоновый слушатель пересылает локальным
соединениям. Без Redis работает только локально (для dev и тестов).
"""
import asyncio
import json
import os
from collections import defaultdict

from fastapi import WebSocket

REDIS_URL = os.getenv("REDIS_URL", "")

_connections: dict[str, set[WebSocket]] = defaultdict(set)
_redis = None
_listener_task: asyncio.Task | None = None


async def connect_redis() -> None:
    global _redis, _listener_task
    if REDIS_URL and _redis is None:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        _listener_task = asyncio.create_task(_redis_listener())


async def disconnect_redis() -> None:
    global _redis, _listener_task
    if _listener_task is not None:
        _listener_task.cancel()
        _listener_task = None
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def _redis_listener() -> None:
    pubsub = _redis.pubsub()
    await pubsub.psubscribe("game:*")
    try:
        async for msg in pubsub.listen():
            if msg.get("type") == "pmessage":
                channel = msg["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode()
                game_id = channel.split(":", 1)[1]
                await _send_local(game_id, msg["data"])
    finally:
        await pubsub.aclose()


async def register(game_id: str, ws: WebSocket) -> None:
    _connections[game_id].add(ws)


async def unregister(game_id: str, ws: WebSocket) -> None:
    _connections[game_id].discard(ws)


def state_message(state) -> str:
    """Сериализовать снапшот в WS-сообщение (json)."""
    return json.dumps({"type": "state", "state": state.model_dump(mode="json")}, ensure_ascii=False)


async def _send_local(game_id: str, text: str) -> None:
    for ws in list(_connections.get(game_id, ())):
        try:
            await ws.send_text(text)
        except Exception:
            _connections[game_id].discard(ws)


async def broadcast(game_id: str, state) -> None:
    """Разослать новый снапшот всем наблюдателям партии."""
    text = state_message(state)
    if _redis is not None:
        await _redis.publish(f"game:{game_id}", text)
    else:
        await _send_local(game_id, text)