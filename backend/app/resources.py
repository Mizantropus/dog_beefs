"""Ресурсы: деньги, компромат, взрывчатка.

Операции стандартного действия «Поднять / Положить». Каждая функция
валидирует (бросает CommandError) и мутирует переданное состояние.
Из Ч1.9 они будут вызываться при розыгрыше карты.

Правила:
- общее условие подбора: хотя бы один ваш пёс в районе;
- деньги забираются сразу все;
- компромат на себя поднимается с проверкой авторитета (5–6 — успех);
- компромат на других подбирается без проверки;
- взрывчатка: своя (любая) и чужая неактивная — просто забираются;
  чужая активная — разминирование с проверкой боя (чёрная грань — успех).
"""
from . import reactions, tokens
from .errors import CommandError
from .rng import Rng
from .state import GameState


def _district(state: GameState, district_id: int):
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    return d


def _require_dog(state: GameState, seat: int, district_id: int):
    d = _district(state, district_id)
    if d.dogs.get(seat, 0) < 1:
        raise CommandError("Нужен хотя бы один ваш пёс в районе")
    return d


# --- деньги ---

def take_money(state: GameState, seat: int, district_id: int) -> None:
    d = _require_dog(state, seat, district_id)
    if d.money <= 0:
        raise CommandError("В районе нет денег")
    state.players[seat].money += d.money
    d.money = 0


def place_money(state: GameState, seat: int, district_id: int, amount: int) -> None:
    d = _require_dog(state, seat, district_id)
    if amount <= 0:
        raise CommandError("Сумма должна быть больше нуля")
    if state.players[seat].money < amount:
        raise CommandError("Недостаточно денег")
    state.players[seat].money -= amount
    d.money += amount


# --- компромат ---

def lift_kompromat_self(state: GameState, rng: Rng, seat: int, district_id: int) -> None:
    """Снять компромат на себя: проверка авторитета 5–6."""
    d = _require_dog(state, seat, district_id)
    if seat not in d.kompromat:
        raise CommandError("Здесь нет компромата на вас")
    face = rng.roll(6)
    state.pending_kompromat = {"seat": seat, "face": face, "kind": "lift_kompromat", "district_id": district_id}
    reactions.open_roll(state, seat, "authority")


def take_kompromat_other(state: GameState, seat: int, district_id: int, target_seat: int) -> None:
    """Подобрать чужой компромат (без проверки)."""
    d = _require_dog(state, seat, district_id)
    if target_seat == seat:
        raise CommandError("Это компромат на вас — нужна проверка авторитета")
    if target_seat not in d.kompromat:
        raise CommandError("Здесь нет такого компромата")
    d.kompromat.remove(target_seat)
    state.players[seat].kompromat.append(target_seat)


def place_kompromat(state: GameState, seat: int, district_id: int, target_seat: int) -> None:
    """Положить компромат из запаса в район."""
    d = _require_dog(state, seat, district_id)
    if target_seat not in state.players[seat].kompromat:
        raise CommandError("У вас нет такого компромата")
    state.players[seat].kompromat.remove(target_seat)
    d.kompromat.append(target_seat)


# --- взрывчатка ---

def mine(state: GameState, seat: int, district_id: int, active: bool = False) -> None:
    """Заложить взрывчатку (active=True — заминировать, False — просто положить)."""
    d = _require_dog(state, seat, district_id)
    if state.players[seat].explosives < 1:
        raise CommandError("У вас нет взрывчатки")
    state.players[seat].explosives -= 1
    d.explosives.append({"owner": seat, "active": active})


def take_explosive(state: GameState, seat: int, district_id: int) -> None:
    """Забрать взрывчатку: сначала неактивную (любую), затем свою активную.

    Чужую активную так забрать нельзя — только разминировать (demine).
    """
    d = _require_dog(state, seat, district_id)
    for ex in d.explosives:
        if not ex["active"]:
            d.explosives.remove(ex)
            state.players[seat].explosives += 1
            return
    for ex in d.explosives:
        if ex["owner"] == seat:
            d.explosives.remove(ex)
            state.players[seat].explosives += 1
            return
    raise CommandError("Нет взрывчатки, которую можно просто забрать")


def demine(state: GameState, rng: Rng, seat: int, district_id: int) -> None:
    """Разминировать чужую активную взрывчатку (чёрная грань — успех, иначе взрыв)."""
    d = _require_dog(state, seat, district_id)
    for ex in d.explosives:
        if ex["owner"] != seat and ex["active"]:
            if tokens.is_black_face(state, seat, rng.roll(6)):
                d.explosives.remove(ex)
                state.players[seat].explosives += 1
            else:
                d.explosives.remove(ex)  # осечка — детонация
                explode(state, rng, district_id, ex["owner"])
            return
    raise CommandError("Нет чужой активной взрывчатки")


def explode_event(state: GameState, district_id: int) -> None:
    """Взрыв от карты события: за каждого пса — проверка авторитета (1–3 = гибель)."""
    d = state.districts[district_id]
    queue = []
    for seat in sorted(d.dogs.keys()):
        for _ in range(d.dogs[seat]):
            queue.append(seat)
    if not queue:
        return
    state.pending_event_explosion = {"district_id": district_id, "queue": queue, "idx": 0, "value": None}


def event_explosion_roll(state: GameState, rng: Rng, seat: int) -> None:
    """Бросок проверки авторитета за текущего пса."""
    pe = state.pending_event_explosion
    if pe is None:
        raise CommandError("Нет взрыва")
    if pe["queue"][pe["idx"]] != seat:
        raise CommandError("Не ваш бросок")
    if pe["value"] is not None:
        raise CommandError("Сначала нажмите ОК")
    face = rng.roll(6)
    pe["face"] = face
    pe["value"] = tokens.authority_value(state, seat, face)
    from . import reactions
    reactions.open_roll(state, seat, "explosion")


def event_explosion_ok(state: GameState, rng: Rng, seat: int) -> None:
    """Применить результат (1–3 — гибель, с окном «Броник») и перейти дальше."""
    pe = state.pending_event_explosion
    if pe is None:
        raise CommandError("Нет взрыва")
    if pe["queue"][pe["idx"]] != seat:
        raise CommandError("Не ваш бросок")
    if pe["value"] is None:
        raise CommandError("Сначала бросьте кубик")
    district_id = pe["district_id"]
    if pe["value"] <= 3:
        from . import reactions
        if reactions.open_dog_killed(state, seat, district_id, resume="event_explosion"):
            return  # окно броника; close убьёт/спасёт и продолжит
        _remove_dog(state, seat, district_id)
    _advance_event_explosion(state)


def _advance_event_explosion(state: GameState) -> None:
    pe = state.pending_event_explosion
    if pe is None:
        return
    pe["idx"] += 1
    pe["value"] = None
    pe["face"] = None
    if pe["idx"] >= len(pe["queue"]):
        district_id = pe["district_id"]
        state.pending_event_explosion = None
        from . import reactions
        reactions.trigger_cleanup(state, [district_id])


def resume_event_explosion(state: GameState, pending: dict) -> None:
    """Продолжить взрыв после окна «Броник»."""
    _advance_event_explosion(state)


def explode(state: GameState, rng: Rng, district_id: int, owner: int = 0) -> None:
    """Детонация: владелец бросает кубик за каждого пса (грань атаки или чёрная — гибель; броник спасает)."""
    d = state.districts[district_id]
    queue = [seat for seat in list(d.dogs.keys()) for _ in range(d.dogs[seat])]
    _explode_step(state, rng, district_id, owner, queue)


def _explode_step(state: GameState, rng: Rng, district_id: int, owner: int, queue: list[int]) -> None:
    if not queue:
        from . import reactions
        reactions.open_combat_ended(state, district_id)
        return
    seat = queue[0]
    face = rng.roll(6)
    if tokens.is_explosion_death_face(state, owner, face):
        if reactions.open_dog_killed(state, seat, district_id, resume="explosion",
                                     owner=owner, queue=queue[1:]):
            return  # окно броника; close -> kill + resume_explosion
        _remove_dog(state, seat, district_id)
    _explode_step(state, rng, district_id, owner, queue[1:])


def resume_explosion(state: GameState, rng: Rng, pending: dict) -> None:
    """Продолжить взрыв после окна реакции (armor)."""
    _explode_step(state, rng, pending["district_id"], pending["owner"], pending["queue"])


def _remove_dog(state: GameState, seat: int, district_id: int) -> None:
    d = state.districts[district_id]
    d.dogs[seat] -= 1
    if d.dogs[seat] <= 0:
        del d.dogs[seat]