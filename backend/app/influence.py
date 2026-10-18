"""Влияние и победа.

Условия получения влияния (ПО = victory_points, победа при 6 ПО):
- фаза розыгрыша: постройка, снос здания, победа в бою;
- разбор полётов: «Контроль» и «Подпольная сеть»;
- штраф: шелудивый в каждом активном районе -> все теряют 1 ПО;
- отстающие получают компромат на себя (разница с лидером).
"""
from .buildings import controller
from .state import GameState, Phase

VICTORY_POINTS_TO_WIN = 6


def gain_influence(state: GameState, seat: int, amount: int = 1) -> None:
    """Начислить ПО: вытянуть жетон из мешка, +1 ПО; жетон ждёт обмена (ChooseInfluenceToken)."""
    for _ in range(amount):
        token = state.influence_bag.pop() if state.influence_bag else None
        state.players[seat].victory_points += 1
        if token is not None:
            state.pending_influence.append({"seat": seat, "token": token})


def check_win(state: GameState) -> bool:
    """Если кто-то набрал 6 ПО — партия завершается. Возвращает True при победе."""
    winners = [p.seat for p in state.players if p.victory_points >= VICTORY_POINTS_TO_WIN]
    if winners and state.phase != Phase.FINISHED:
        state.phase = Phase.FINISHED
        state.winners = winners
    return bool(winners)


# --- влияние в фазе розыгрыша ---

def influence_for_build(state: GameState, seat: int, district_id: int) -> None:
    d = state.districts[district_id]
    if seat not in d.kompromat:
        gain_influence(state, seat, 1)


def influence_for_destroy(state: GameState, seat: int, district_id: int) -> None:
    d = state.districts[district_id]
    if seat in d.kompromat:
        return  # компромат на вас — нет влияния
    gain_influence(state, seat, 1)
    d.kompromat.append(seat)  # положить компромат на себя


def influence_for_combat(state: GameState) -> None:
    lc = state.last_combat
    if lc is None or lc["winner"] is None:
        return
    winner = lc["winner"]
    d = state.districts[lc["district_id"]]
    if winner in d.kompromat:
        return  # компромат на вас — нет влияния
    if lc["vs_mangy"] and lc.get("initial_mangy", 0) < 3:
        return  # нужно победить минимум троих шелудивых
    gain_influence(state, winner, 1)
    d.kompromat.append(winner)  # положить компромат на себя


# --- условия в разборе полётов ---

def control_districts(state: GameState, seat: int) -> list[int]:
    """Районы «Контроля»: вы контролируете, есть чужие фишки, нет компромата на вас."""
    out = []
    for d in state.districts.values():
        if seat in d.kompromat:
            continue
        if controller(state, d.id) != seat:
            continue
        has_enemy = any(
            other != seat and (d.dogs.get(other, 0) > 0 or d.building_owner == other)
            for other in range(state.player_count)
        )
        if has_enemy:
            out.append(d.id)
    return out


def control_score(state: GameState, seat: int) -> int:
    return len(control_districts(state, seat))


def network_districts(state: GameState, seat: int) -> list[int]:
    """Районы «Подпольной сети»: ваши фишки + шелудивые, нет компромата на вас."""
    out = []
    for d in state.districts.values():
        if seat in d.kompromat:
            continue
        has_mine = d.dogs.get(seat, 0) > 0 or d.building_owner == seat
        if has_mine and d.mangy >= 1:
            out.append(d.id)
    return out


def network_score(state: GameState, seat: int) -> int:
    return len(network_districts(state, seat))


def _unique_top(scores: dict[int, int]) -> int | None:
    if not scores:
        return None
    top = max(scores.values())
    if top <= 0:
        return None
    holders = [s for s, v in scores.items() if v == top]
    return holders[0] if len(holders) == 1 else None


def apply_penalty(state: GameState) -> None:
    """Штраф: шелудивый в каждом активном районе -> все теряют 1 ПО."""
    active = state.board_districts or list(state.districts.keys())
    if all(state.districts[d].mangy >= 1 for d in active):
        for p in state.players:
            p.victory_points = max(0, p.victory_points - 1)
        state.pending_penalty = {"acked": []}


def distribute_kompromat(state: GameState) -> None:
    """Отстающие получают компромат на себя (разница с лидером)."""
    leader = max(p.victory_points for p in state.players)
    for p in state.players:
        deficit = leader - p.victory_points
        if deficit > 0:
            p.kompromat.extend([p.seat] * deficit)


def end_round_influence(state: GameState) -> None:
    """Разбор полётов: влияние за «Контроль» и «Подпольную сеть» + штраф.

    Получивший влияние кладёт компромат на себя в район, давший очко;
    при двух очках — в разные районы (если это возможно).
    """
    n = state.player_count
    control_winner = _unique_top({s: control_score(state, s) for s in range(n)})
    network_winner = _unique_top({s: network_score(state, s) for s in range(n)})
    if control_winner is not None:
        gain_influence(state, control_winner, 1)
    if network_winner is not None:
        gain_influence(state, network_winner, 1)
    used: set[int] = set()
    if control_winner is not None:
        _place_debrief_kompromat(state, control_winner, control_districts(state, control_winner), used)
    if network_winner is not None:
        _place_debrief_kompromat(state, network_winner, network_districts(state, network_winner), used)
    apply_penalty(state)


def _place_debrief_kompromat(state: GameState, seat: int, districts: list[int], used: set[int]) -> None:
    """Положить компромат на себя в первый подходящий район (без повторов)."""
    for d_id in districts:
        if d_id in used:
            continue
        if seat in state.districts[d_id].kompromat:
            continue
        state.districts[d_id].kompromat.append(seat)
        used.add(d_id)
        return