"""Загрузка каталога карт и поля из JSON в БД (идемпотентно: очистить + вставить)."""
import asyncio
import json
from pathlib import Path

from sqlalchemy import delete, text

from .db import Base, async_session, engine
from .models import (ActionCard, ActionDefinition, BoardLayout, District,
                     EventCard, Gang, HexEdge)

DATA_DIR = Path(__file__).parent / "data"


def load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


async def _reload(session, model, rows):
    await session.execute(delete(model))
    session.add_all([model(**r) for r in rows])


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # миграция для старых БД: добавить недостающие колонки (идемпотентно)
        await conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS names JSON"))

    async with async_session() as session:
        await _reload(session, District, load("districts.json"))
        await _reload(session, ActionDefinition, load("action_definitions.json"))
        await _reload(session, ActionCard, load("action_cards.json"))
        await _reload(session, EventCard, load("event_cards.json"))
        await _reload(session, Gang, load("gangs.json"))
        await _reload(session, BoardLayout, load("board_layouts.json"))
        await _reload(session, HexEdge, load("hex_edges.json"))
        await session.commit()

    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())