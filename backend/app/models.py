"""Модели каталога игры (статический справочник) + гекс-сетка + партии."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class District(Base):
    """Район города (гекс с номером 1–13)."""

    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    type_key: Mapped[str] = mapped_column(String(32))
    build_cost: Mapped[int] = mapped_column(Integer)
    income: Mapped[int] = mapped_column(Integer)
    ability: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ActionDefinition(Base):
    """Отдельное действие (стандартное или ситуативное).

    Если действие даёт выбор из поддействий (например, «Поднять / Положить»),
    поддействия лежат в `options`; у атомарных действий `options` = NULL.
    """

    __tablename__ = "action_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[str] = mapped_column(String(16))  # standard | situational
    title: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ActionCard(Base):
    """Карта действия: верх (стандартное) + низ (ситуативное) + маркер 2/3/4."""

    __tablename__ = "action_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_group: Mapped[str] = mapped_column(String(4))  # "2" | "3" | "4"
    standard_key: Mapped[str] = mapped_column(String(64))
    situational_key: Mapped[str] = mapped_column(String(64))
    draft: Mapped[bool] = mapped_column(Boolean, default=True)


class EventCard(Base):
    """Карта события."""

    __tablename__ = "event_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text, default="")
    player_group: Mapped[str] = mapped_column(String(4))
    draft: Mapped[bool] = mapped_column(Boolean, default=True)


class Gang(Base):
    """Банда (способности — позже, на этапе асимметрии)."""

    __tablename__ = "gangs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    ability_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft: Mapped[bool] = mapped_column(Boolean, default=True)


class BoardLayout(Base):
    """Раскладка поля на N игроков: какие гексы участвуют."""

    __tablename__ = "board_layouts"

    player_count: Mapped[int] = mapped_column(Integer, primary_key=True)  # 2 | 3 | 4
    districts: Mapped[list] = mapped_column(JSON)  # номера гексов, напр. [1..7]


class HexEdge(Base):
    """Ребро между двумя гексами в раскладке.

    kind = "land"  — обычное соседство (проход свободный);
    kind = "river" — разделены рекой (нужен мост; мост можно сломать/починить).
    """

    __tablename__ = "hex_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_count: Mapped[int] = mapped_column(Integer)  # 2 | 3 | 4
    a: Mapped[int] = mapped_column(Integer)  # номер гекса
    b: Mapped[int] = mapped_column(Integer)  # номер соседнего гекса
    kind: Mapped[str] = mapped_column(String(8))  # land | river
    draft: Mapped[bool] = mapped_column(Boolean, default=True)


class Game(Base):
    """Партия: версионированный снапшот состояния (JSON) + метаданные."""

    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # uuid
    version: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | finished
    state: Mapped[dict] = mapped_column(JSON)  # GameState.model_dump(mode="json")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Room(Base):
    """Комната (лобби) до начала партии: вход по ссылке без аккаунтов."""

    __tablename__ = "rooms"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)   # короткий код для ссылки
    player_count: Mapped[int] = mapped_column(Integer)               # 2 | 3 | 4
    status: Mapped[str] = mapped_column(String(16), default="waiting")  # waiting | playing | finished
    host_token: Mapped[str] = mapped_column(String(64))              # токен хоста (он же игрок seat 0)
    seats: Mapped[list] = mapped_column(JSON)                        # list[str|None], индекс = seat
    game_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Move(Base):
    """Запись журнала ходов: одна команда, применённая к партии."""

    __tablename__ = "moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)   # версия снапшота ПОСЛЕ команды
    seat: Mapped[int] = mapped_column(Integer)      # кто сделал ход
    command: Mapped[dict] = mapped_column(JSON)     # сериализованная команда
    summary: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
