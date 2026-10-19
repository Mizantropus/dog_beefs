"""Хранилище партий: версионированные снапшоты с оптимистичной блокировкой."""
from sqlalchemy import update

from .db import async_session
from .models import Game, Move
from .state import GameState


class VersionConflict(Exception):
    """Снапшот устарел: кто-то уже изменил партию новее нашей версии."""


def summarize(command: dict, state: GameState | None = None) -> str:
    """Короткое человекочитаемое описание хода (для журнала)."""
    seat = command.get("seat")
    if state is not None and isinstance(seat, int) and 0 <= seat < len(state.players):
        who = state.players[seat].name or f"Игрок {seat + 1}"
    elif isinstance(seat, int):
        who = f"Игрок {seat + 1}"
    else:
        who = "Игрок"
    t = command.get("type")
    labels = {
        "pass": "пас",
        "end_turn": "завершил ход",
        "pick_draft": "взял карту в драфте",
        "discard_card": "сбросил карту",
        "play_card": "сыграл карту действия",
        "play_kompromat": "сыграл компромат",
        "start_combat": "начал бой",
        "roll_combat": "бросил кубик",
        "resolve_combat": "применил бросок",
        "use_ability": "использовал свойство здания",
        "play_situational": "сыграл ситуативное действие",
        "pass_reaction": "пропустил реакцию",
        "choose_influence": "разыграл жетон влияния",
        "resolve_kompromat": "разрешил компромат",
        "resolve_peek": "завершил просмотр событий",
        "pick_discard_buy": "выбрал карту из сброса",
        "resolve_swap": "завершил обмен карты",
        "resolve_place": "выбрал район",
        "resolve_move": "завершил перемещение",
        "resolve_move_choice": "выбрал район после «Проход запрещён»",
        "event_explosion": "бросок при взрыве",
        "resolve_token_swap": "обменял жетон влияния",
        "may_event": "действие в событии",
        "kazino": "ход в казино",
        "resolve_choice": "сделал выбор",
        "event_roll": "бросок в событии",
        "ack_combat_result": "подтвердил результат боя",
        "ack_mangy_roll": "подтвердил бросок шелудивых",
        "ack_penalty": "подтвердил штраф",
        "ack_event": "подтвердил карту события",
        "advance_phase": "сменил фазу",
    }
    return f"{who}: {labels.get(t, t)}"


class GameStore:
    async def create(self, state: GameState) -> GameState:
        async with async_session() as session:
            session.add(Game(
                id=state.id,
                version=state.version,
                status="active",
                state=state.model_dump(mode="json"),
            ))
            await session.commit()
        return state

    async def load(self, game_id: str) -> GameState | None:
        async with async_session() as session:
            game = await session.get(Game, game_id)
            if game is None:
                return None
            return GameState.model_validate(game.state)

    async def save(self, state: GameState) -> GameState:
        """Сохраняет снапшот, проверяя, что в БД лежит ровно версия-1.

        Это CAS (compare-and-swap): если другая запись уже повысила версию,
        UPDATE затронет 0 строк — бросаем VersionConflict.
        """
        async with async_session() as session:
            result = await session.execute(
                update(Game)
                .where(Game.id == state.id, Game.version == state.version - 1)
                .values(version=state.version, state=state.model_dump(mode="json"))
            )
            await session.commit()
            if result.rowcount == 0:
                raise VersionConflict(f"Game {state.id} version conflict")
        return state

    async def log_move(self, game_id: str, version: int, seat: int,
                       command: dict, summary: str) -> None:
        """Дописать ход в журнал партии."""
        async with async_session() as session:
            session.add(Move(game_id=game_id, version=version, seat=seat,
                             command=command, summary=summary))
            await session.commit()