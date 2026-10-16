"""Модель игрового состояния (домен, чистые Pydantic-модели).

Это «снапшот» одной партии в конкретный момент. Состояние неизменяемо:
любое изменение порождает НОВЫЙ объект с увеличенным `version`.
Сериализуется в JSON и хранится в таблице `games` (см. store.py).
"""
import uuid
from enum import Enum

from pydantic import BaseModel, Field

from .rng import Rng


class Phase(str, Enum):
    SETUP = "setup"          # подготовка (выбор логова и т.п.)
    DRAFT = "draft"          # драфт карт
    PLAY = "play"            # розыгрыш карт и компромата
    END_ROUND = "end_round"  # разбор полётов
    FINISHED = "finished"    # партия завершена


class DeckState(BaseModel):
    """Колода: добор (рубашкой вниз) и сброс (лицевой стороной вверх)."""
    draw: list[str] = []
    discard: list[str] = []


class DraftState(BaseModel):
    """Состояние драфта (фаза DRAFT)."""
    deal: int = 1                       # 1 или 2 (две сделки по 4 карты)
    hand: dict[int, list[str]] = {}     # seat -> карты, из которых выбирает
    picked: list[int] = []              # кто уже выбрал в текущем подраунде


class PlayerState(BaseModel):
    """Состояние одного игрока."""
    seat: int                                # место за столом 0..N-1
    name: str = ""                           # имя игрока (из лобби)
    money: int = 1500                        # деньги в личном запасе
    hand: list[str] = []                     # карты действий на руке (id карт)
    explosives: int = 1                      # взрывчатка в личном запасе
    kompromat: list[int] = []                # жетоны компромата на руках (значение = целевой seat)
    authority_line: list[str] = ["dummy", "place_money", "place_explosive", "take_money", "swap_card", "take_resource"]  # жетоны авторитета (ключи)
    combat_line: list[str] = ["attack", "gop", "self_gop", "rob", "move_dog", "leave_trace"]  # стартовые жетоны боя
    victory_points: int = 0                  # победные очки (6 = победа)
    used_abilities: list[int] = []            # районы, чьё свойство уже использовано в этот ход
    has_played: bool = False                  # сделан ли ход (карта/компромат/пас) в этот ход
    played_standard: bool = False              # разыграно ли стандартное действие (даёт право на свойства зданий)


class DistrictState(BaseModel):
    """Состояние одного района (гекса) на поле."""
    id: int
    building_owner: int | None = None        # seat владельца здания (None — пусто)
    dogs: dict[int, int] = {}                # seat -> число псов
    mangy: int = 0                           # число шелудивых
    kompromat: list[int] = []                # чей компромат лежит здесь (target seats)
    explosives: list[dict] = []              # [{"owner": seat, "active": bool}]
    money: int = 0                           # деньги, лежащие в районе
    build_cost: int = 0                      # цена постройки (из каталога)
    income: int = 0                          # доход за ход владельцу (из каталога)
    ability: dict | None = None              # свойство района (из каталога)


class CombatState(BaseModel):
    """Состояние боя (вложенный под-процесс фазы розыгрыша)."""
    district_id: int
    attacker: int                            # кто начал бой
    defender: int | None = None              # None => бой с шелудивыми
    next_is_attacker: bool = True            # чей ход: True=атакующий, False=защитник/шелудивые
    pending: dict | None = None              # {"face": int, "opposite": int} — бросок в ожидании переворота
    mangy_killed_or_recruited: int = 0       # убито/завербовано шелудивых (для условия влияния)


class GameState(BaseModel):
    """Полный снапшот партии."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_count: int
    seed: int = 0                            # сид партии
    rng_state: list = []                     # сериализованное состояние ГСЧ (app.rng.Rng)
    version: int = 0                         # версия снапшота (растёт на каждом изменении)
    round: int = 1                           # номер раунда
    phase: Phase = Phase.SETUP
    first_seat: int = 0                      # кто ходит первым в фазе розыгрыша (ротируется)
    current_seat: int = 0                    # чей ход
    passes_in_a_row: int = 0                 # подряд пасов (все спасовали -> конец фазы)
    draft: DraftState | None = None          # состояние драфта (только в фазе DRAFT)
    combat: CombatState | None = None        # текущий бой (None — боя нет)
    last_combat: dict | None = None          # результат последнего боя (для Ч1.8)
    winners: list[int] = []                  # победители (seat) при завершении партии
    board_districts: list[int] = []          # активные районы на поле (1..7/10/13)
    cards: dict[str, dict] = {}              # карты действий в снапшоте: id -> {standard_key, situational_key}
    edges: list[dict] = []                   # рёбра гекс-сетки этой партии: {a, b, kind}
    debtors: list[int] = []                  # игроки, взявшие «Кредит» (для события «Коллекторы»)
    pending_reaction: dict | None = None     # окно реакции: {trigger, responded, ...}
    influence_bag: list[str] = []            # мешок наградных жетонов влияния (40)
    pending_influence: list[dict] = []       # очередь жетонов влияния для обмена: {seat, token}
    pending_kompromat: dict | None = None   # белый жетон -> выбор свойства района
    pending_swap: dict | None = None         # выбор карты сброса: {seat, pool, swap}
    credit_played: bool = False               # было ли разыграно событие «Кредит»
    pending_may_event: dict | None = None      # добровольное событие: {slug, acted, done}
    pending_kazino: dict | None = None         # казино: {pot, results, order, idx, rolled, rerolled}
    pending_choice: dict | None = None         # выбор игрока: {seat, kind, options, context}
    pending_place: dict | None = None          # жетон авторитета: выбор района {seat, kind}
    pending_move: dict | None = None           # жетон авторитета «Перемещение»: {seat}
    pending_token_swap: dict | None = None     # обмен жетона влияния: {seat, drawn}
    pending_move_choice: dict | None = None    # выбор после «Проход запрещён»: {seat, from_district, dogs_count, mangy_count, excluded_to}
    cleanup_queue: list[int] = []               # очередь районов для окон «Уборка мусора»
    pending_event_explosion: dict | None = None  # взрыв события: {district_id, queue, idx, value}
    pending_penalty: dict | None = None         # штраф: {acked}
    pending_combat_result: dict | None = None  # результат жетона боя: {roller, effect}
    pending_event_roll: dict | None = None    # пошаговый бросок в событии: {slug, order, idx, results, rolled, target}
    pending_peek: dict | None = None        # Радиостанция: просмотр 2 карт событий
    pending_event: dict | None = None         # карта события для подтверждения: {slug, acked}
    players: list[PlayerState] = []
    districts: dict[int, DistrictState] = {}  # номер гекса -> район
    action_deck: DeckState = DeckState()
    event_deck: DeckState = DeckState()
    broken_bridges: list[list[int]] = []      # сломанные мосты: пары [a, b]


# Районы, куда по подготовке кладутся стартовые 200$ (см. правила, подготовка п.5).
SETUP_MONEY_DISTRICTS = [1, 2, 3, 8, 11]


def new_game(player_count: int, seed: int = 0) -> GameState:
    """Начальное состояние партии (базовая подготовка).

    Колоды и драфт собираются в app.round.prepare_game.
    """
    if player_count not in (2, 3, 4):
        raise ValueError("player_count must be 2, 3 or 4")

    players = [
        PlayerState(seat=i, money=1500, explosives=1, kompromat=[i])
        for i in range(player_count)
    ]
    districts = {i: DistrictState(id=i) for i in range(1, 14)}
    for d in SETUP_MONEY_DISTRICTS:
        districts[d].money = 200

    rng = Rng(seed)

    return GameState(
        player_count=player_count,
        seed=seed,
        rng_state=rng.state(),
        players=players,
        districts=districts,
    )