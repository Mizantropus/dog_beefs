"""Жизненный цикл раунда и подготовка партии.

Раунд: DRAFT (драфт, 2 сделки по 4 карты) -> PLAY (розыгрыш/пасы) ->
END_ROUND (разбор полётов, структурная часть) -> новый раунд.

Влияние, штраф и события добавляются в END_ROUND позже (Ч1.8 / Ч1.10).
"""
from . import events, influence, tokens
from .rng import Rng
from .state import DraftState, GameState, Phase, new_game


def _deal(state: GameState, count: int) -> list[str]:
    """Выдать до count карт из добора действий (сколько есть — без IndexError)."""
    out = []
    draw = state.action_deck.draw
    for _ in range(count):
        if not draw:
            break
        out.append(draw.pop())
    return out


def groups_for_player_count(n: int) -> set[str]:
    """Какие маркеры карт участвуют при N игроках (по правилам подготовки)."""
    if n == 2:
        return {"2"}
    if n == 3:
        return {"2", "3"}
    if n == 4:
        return {"2", "3", "4"}
    raise ValueError("player_count must be 2, 3 or 4")


def build_action_deck(cards, n: int) -> list[str]:
    """Список id карт действий для колоды на N игроков."""
    allowed = groups_for_player_count(n)
    return [str(c.id) for c in cards if c.player_group in allowed]


def build_event_deck(cards, n: int) -> list[str]:
    """Список slug карт событий для колоды на N игроков."""
    allowed = groups_for_player_count(n)
    return [c.slug for c in cards if c.player_group in allowed]


def prepare_game(n: int, seed: int, action_cards, event_cards, districts, hex_edges) -> GameState:
    """Собрать партию: колоды + тасовка + первый драфт."""
    state = new_game(n, seed=seed)
    for d in districts:
        st = state.districts[d.id]
        st.build_cost = d.build_cost
        st.income = d.income
        st.ability = d.ability
    state.board_districts = list(range(1, {2: 7, 3: 10, 4: 13}[n] + 1))
    # стартовые деньги (1,2,3,8,11) — только в районах, которые есть на поле
    for d in list(state.districts.keys()):
        if d not in state.board_districts:
            state.districts[d].money = 0
    state.cards = {str(c.id): {"standard_key": c.standard_key, "situational_key": c.situational_key} for c in action_cards}
    state.edges = [{"a": e.a, "b": e.b, "kind": e.kind} for e in hex_edges if e.player_count == n]
    rng = Rng.from_state(state.rng_state)
    state.action_deck.draw = rng.shuffle(build_action_deck(action_cards, n))
    state.event_deck.draw = rng.shuffle(build_event_deck(event_cards, n))
    state.influence_bag = rng.shuffle(tokens.build_influence_bag())
    # стартовая расстановка: логова (случайно) + псы + порядок жетонов боя
    lairs = [d.id for d in districts if d.type_key == "logovo" and d.id in state.board_districts]
    lairs = rng.shuffle(lairs)
    for seat in range(n):
        lid = lairs[seat]
        state.districts[lid].building_owner = seat
        state.districts[lid].dogs[seat] = n
    for p in state.players:
        p.combat_line = rng.shuffle(p.combat_line)
    start_round(state, rng)
    state.rng_state = rng.state()
    return state


def start_round(state: GameState, rng: Rng) -> None:
    """Начать раунд: при необходимости перетасовать сброс в добор, раздать драфт."""
    if not state.action_deck.draw:
        state.action_deck.draw = rng.shuffle(state.action_deck.discard)
        state.action_deck.discard = []
    state.phase = Phase.DRAFT
    state.current_seat = state.first_seat
    state.passes_in_a_row = 0
    for p in state.players:
        p.used_abilities = []
        p.has_played = False
        p.played_standard = False
    hand = {}
    for seat in range(state.player_count):
        hand[seat] = _deal(state, 4)
    state.draft = DraftState(deal=1, hand=hand, picked=[])


def advance_draft(state: GameState, rng: Rng) -> None:
    """После того как все выбрали карту: передать/сбросить, продолжить или завершить."""
    d = state.draft
    n = state.player_count
    remaining = len(d.hand[0]) if d.hand else 0

    if remaining >= 2:
        # передать остаток следующему игроку по часовой стрелке
        old = dict(d.hand)
        for seat in range(n):
            d.hand[seat] = old[(seat - 1) % n]
    else:
        # осталась 1 карта у каждого — сбросить её
        for seat in range(n):
            state.action_deck.discard.extend(d.hand[seat])
            d.hand[seat] = []
        if d.deal == 1:
            d.deal = 2
            for seat in range(n):
                d.hand[seat] = _deal(state, 4)
        else:
            state.draft = None
            state.phase = Phase.PLAY
            state.current_seat = state.first_seat
            state.passes_in_a_row = 0

    d.picked = []


def end_round(state: GameState, rng: Rng) -> None:
    """Разбор полётов: влияние + штраф, сброс рук, победа/компромат, новый раунд."""
    # 1. влияние (контроль/сеть) + штраф
    influence.end_round_influence(state)
    # 2. одна карта события
    events.draw_and_resolve_event(state, rng, state.first_seat)
    # 3. сброс карт с рук
    for p in state.players:
        state.action_deck.discard.extend(p.hand)
        p.hand = []
    # 4. проверка победы
    if influence.check_win(state):
        return
    # 5. компромат отстающим
    influence.distribute_kompromat(state)
    # 6. новый раунд
    state.first_seat = (state.first_seat + 1) % state.player_count
    state.round += 1
    start_round(state, rng)


def next_turn(state: GameState) -> None:
    """Передать ход следующему игроку и сбросить его счётчик использованных свойств."""
    state.current_seat = (state.current_seat + 1) % state.player_count
    state.players[state.current_seat].used_abilities = []
    state.players[state.current_seat].has_played = False
    state.players[state.current_seat].played_standard = False