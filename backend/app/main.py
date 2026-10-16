"""Точка входа FastAPI-приложения «Собачьи тёрки»."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import realtime, seed
from .db import engine
from .routers import board, catalog, games, rooms, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed.seed()  # создать таблицы и загрузить каталог
    await realtime.connect_redis()
    yield
    await realtime.disconnect_redis()
    await engine.dispose()


app = FastAPI(title="Собачьи тёрки API", version="0.4.0", lifespan=lifespan)
app.include_router(catalog.router)
app.include_router(board.router)
app.include_router(games.router)
app.include_router(rooms.router)
app.include_router(ws.router)


@app.get("/")
def root() -> dict:
    return {"app": "Собачьи тёрки", "status": "ok"}


@app.get("/api/hello")
def hello() -> dict:
    return {"message": "Бэкенд работает"}