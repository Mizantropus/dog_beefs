"""Гекс-сетка и мосты: соседство, проходимость, перемещение, снос/починка мостов."""
from .errors import CommandError
from .state import GameState


def _key(a: int, b: int) -> list[int]:
    return sorted([a, b])


def edge_between(state: GameState, a: int, b: int):
    for e in state.edges:
        if (e["a"] == a and e["b"] == b) or (e["a"] == b and e["b"] == a):
            return e
    return None


def is_bridge(state: GameState, a: int, b: int) -> bool:
    e = edge_between(state, a, b)
    return e is not None and e["kind"] == "river"


def is_broken(state: GameState, a: int, b: int) -> bool:
    return _key(a, b) in state.broken_bridges


def is_passable(state: GameState, a: int, b: int) -> bool:
    """Можно ли пройти из a в b: суша или река с целым мостом."""
    e = edge_between(state, a, b)
    if e is None:
        return False
    if e["kind"] == "land":
        return True
    return not is_broken(state, a, b)


def neighbors(state: GameState, district_id: int) -> list[int]:
    out = []
    for e in state.edges:
        if e["a"] == district_id:
            other = e["b"]
        elif e["b"] == district_id:
            other = e["a"]
        else:
            continue
        if is_passable(state, district_id, other):
            out.append(other)
    return out


def validate_move(state: GameState, seat: int, from_district: int, to_district: int,
                  dogs_count: int = 0, mangy_count: int = 0) -> None:
    """Проверка легальности перемещения (без применения)."""
    if not is_passable(state, from_district, to_district):
        raise CommandError("Районы не соседствуют или мост сломан")
    d = state.districts.get(from_district)
    if d is None:
        raise CommandError("Такого района нет")
    if dogs_count < 0 or mangy_count < 0 or (dogs_count == 0 and mangy_count == 0):
        raise CommandError("Укажите, что перемещать")
    if d.dogs.get(seat, 0) < dogs_count:
        raise CommandError("Недостаточно ваших псов")
    if d.mangy < mangy_count:
        raise CommandError("Недостаточно шелудивых")
    if dogs_count == 0 and d.dogs.get(seat, 0) < 1:
        raise CommandError("Чтобы вести шелудивых без псов, нужен ваш пёс в районе")


def move(state: GameState, seat: int, from_district: int, to_district: int,
         dogs_count: int = 0, mangy_count: int = 0) -> None:
    """Переместить своих псов (и/или шелудивых) из района в соседний."""
    validate_move(state, seat, from_district, to_district, dogs_count, mangy_count)
    d = state.districts[from_district]

    if dogs_count > 0:
        d.dogs[seat] -= dogs_count
        if d.dogs[seat] == 0:
            del d.dogs[seat]
    if mangy_count > 0:
        d.mangy -= mangy_count
    t = state.districts[to_district]
    if dogs_count > 0:
        t.dogs[seat] = t.dogs.get(seat, 0) + dogs_count
    if mangy_count > 0:
        t.mangy += mangy_count


def destroy_bridge(state: GameState, seat: int, a: int, b: int) -> None:
    """Разрушить мост между a и b (нужна взрывчатка и присутствие у моста)."""
    if not is_bridge(state, a, b):
        raise CommandError("Здесь нет моста")
    if is_broken(state, a, b):
        raise CommandError("Мост уже разрушен")
    if state.districts[a].dogs.get(seat, 0) < 1 and state.districts[b].dogs.get(seat, 0) < 1:
        raise CommandError("Нужно находиться в районе у моста")
    if state.players[seat].explosives < 1:
        raise CommandError("Нужна взрывчатка")
    state.players[seat].explosives -= 1
    state.broken_bridges.append(_key(a, b))
    from . import reactions
    reactions.trigger_cleanup(state, [a, b])


def repair_bridge(state: GameState, seat: int, a: int, b: int) -> None:
    """Починить сломанный мост (500$ и присутствие у моста)."""
    if not is_bridge(state, a, b):
        raise CommandError("Здесь нет моста")
    if not is_broken(state, a, b):
        raise CommandError("Мост не разрушен")
    if state.districts[a].dogs.get(seat, 0) < 1 and state.districts[b].dogs.get(seat, 0) < 1:
        raise CommandError("Нужно находиться в районе у моста")
    if state.players[seat].money < 500:
        raise CommandError("Нужно 500$ на починку")
    state.players[seat].money -= 500
    state.broken_bridges.remove(_key(a, b))