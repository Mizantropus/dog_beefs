"""Ситуативные (реактивные) действия.

Модель: триггер ставит `state.pending_reaction` (пауза). Игроки по очереди
отвечают (PlaySituational / PassReaction). Когда все подходящие ответили —
окно закрывается и применяется отложенный эффект.
"""
from .errors import CommandError
from .rng import Rng
from .state import GameState
from .tokens import OPPOSITE_FACE

TRIGGER_ACTIONS = {
    "combat_started": {"first_strike"},
    "moved_into": {"ambush", "no_entry", "detonate"},
    "dog_killed": {"armor"},
    "combat_ended": {"cleanup"},
    "influence_gained": {"subsidy"},
    "roll": {"reroll"},
}


# Карты с двумя вариантами: родительский ключ -> набор действий.
CARD_OPTIONS = {
    "ambush_first_strike": {"ambush", "first_strike"},
    "subsidy_cleanup": {"subsidy", "cleanup"},
}


def card_actions(card: dict) -> set:
    sk = card.get("situational_key")
    return CARD_OPTIONS.get(sk, {sk})


def has_situational(state: GameState, seat: int, action: str) -> bool:
    for cid in state.players[seat].hand:
        card = state.cards.get(cid)
        if card and action in card_actions(card):
            return True
    return False


def spend_situational(state: GameState, seat: int, action: str) -> None:
    """Сбросить карту с ситуативным действием (или компромат за неё)."""
    for cid in state.players[seat].hand:
        card = state.cards.get(cid)
        if card and action in card_actions(card):
            state.players[seat].hand.remove(cid)
            state.action_deck.discard.append(cid)
            return
    raise CommandError("Нет карты с этим действием")


def eligible(state: GameState, pending: dict) -> list[int]:
    t = pending["trigger"]
    if t == "combat_started":
        d = pending.get("defender")
        return [d] if d is not None else []
    if t == "moved_into":
        dist = state.districts[pending["to_district"]]
        out = []
        for s in range(state.player_count):
            if s == pending["mover"]:
                continue
            if dist.dogs.get(s, 0) > 0 or any(e.get("owner") == s for e in dist.explosives):
                out.append(s)
        return out
    if t == "dog_killed":
        return [pending["seat"]]
    if t == "combat_ended":
        dist = state.districts[pending["district_id"]]
        return [s for s in range(state.player_count)
                if dist.dogs.get(s, 0) > 0 or dist.building_owner == s]
    if t == "influence_gained":
        gainer_vp = state.players[pending["seat"]].victory_points
        return [s for s in range(state.player_count)
                if s != pending["seat"] and state.players[s].victory_points < gainer_vp]
    if t == "roll":
        return [pending["seat"]]
    return []


def next_responder(state: GameState, pending: dict) -> int | None:
    for s in range(state.player_count):
        if s in eligible(state, pending) and s not in pending["responded"]:
            return s
    return None


def can_play(state: GameState, seat: int, action: str, pending: dict) -> bool:
    """Может ли игрок сыграть конкретное действие (карта + условие)."""
    if not has_situational(state, seat, action):
        return False
    if action == "detonate":
        dist = state.districts[pending["to_district"]]
        return any(e.get("owner") == seat and e.get("active") for e in dist.explosives)
    if action in ("ambush", "no_entry"):
        dist = state.districts[pending["to_district"]]
        return dist.dogs.get(seat, 0) > 0
    return True


def try_open(state: GameState, pending: dict) -> bool:
    """Открыть окно реакции, если хоть кто-то может ответить."""
    actions = TRIGGER_ACTIONS[pending["trigger"]]
    for seat in eligible(state, pending):
        if any(can_play(state, seat, a, pending) for a in actions):
            state.pending_reaction = pending
            return True
    return False


def open_combat_started(state, attacker, defender, district_id) -> bool:
    return try_open(state, {"trigger": "combat_started", "attacker": attacker,
                            "defender": defender, "district_id": district_id, "responded": []})


def open_moved_into(state, mover, from_d, to_d, dogs, mangy) -> bool:
    return try_open(state, {"trigger": "moved_into", "mover": mover,
                            "from_district": from_d, "to_district": to_d,
                            "dogs_count": dogs, "mangy_count": mangy, "responded": [],
                            "cancelled": False, "ambush_seat": None, "detonate_seat": None})


def open_dog_killed(state, seat, district_id, resume: str = "combat_roll", **extra) -> bool:
    return try_open(state, {"trigger": "dog_killed", "seat": seat,
                            "district_id": district_id, "responded": [], "saved": False,
                            "resume": resume, **extra})


def open_combat_ended(state, district_id) -> bool:
    return try_open(state, {"trigger": "combat_ended", "district_id": district_id, "responded": []})


def trigger_cleanup(state: GameState, district_ids) -> None:
    """Поставить в очередь окна «Уборка мусора» и открыть первое доступное."""
    for d in district_ids:
        if d not in state.cleanup_queue:
            state.cleanup_queue.append(d)
    _process_cleanup_queue(state)


def _process_cleanup_queue(state: GameState) -> None:
    """Открыть первое доступное окно из очереди (если нет активного окна)."""
    while state.pending_reaction is None and state.cleanup_queue:
        d = state.cleanup_queue.pop(0)
        open_combat_ended(state, d)


def open_influence_gained(state, seat, next_action: str | None = None, **extra) -> bool:
    return try_open(state, {"trigger": "influence_gained", "seat": seat, "responded": [],
                            "next": next_action, **extra})


def open_roll(state, seat, kind: str) -> bool:
    """Окно «Перебросить кубик» (разыгрывает только бросавший)."""
    return try_open(state, {"trigger": "roll", "seat": seat, "kind": kind,
                            "responded": [], "rerolled": False})


def play(state: GameState, rng: Rng, seat: int, action: str) -> None:
    pending = state.pending_reaction
    if pending is None:
        raise CommandError("Нет ожидающей реакции")
    if action not in TRIGGER_ACTIONS[pending["trigger"]]:
        raise CommandError("Это действие не подходит под текущую ситуацию")
    if seat not in eligible(state, pending):
        raise CommandError("Вы не можете ответить сейчас")
    if seat in pending["responded"]:
        raise CommandError("Вы уже ответили")
    _apply(state, rng, seat, action, pending)
    pending["responded"].append(seat)
    _maybe_close(state, rng)


def pass_reaction(state: GameState, rng: Rng, seat: int) -> None:
    pending = state.pending_reaction
    if pending is None:
        raise CommandError("Нет ожидающей реакции")
    if seat not in eligible(state, pending):
        raise CommandError("Вы не можете ответить сейчас")
    if seat in pending["responded"]:
        raise CommandError("Вы уже ответили")
    pending["responded"].append(seat)
    _maybe_close(state, rng)


def _maybe_close(state: GameState, rng: Rng) -> None:
    if next_responder(state, state.pending_reaction) is None:
        close(state, rng)


def close(state: GameState, rng: Rng) -> None:
    pending = state.pending_reaction
    state.pending_reaction = None  # очистить сразу; новая пауза ставится явно ниже
    t = pending["trigger"]
    if t == "combat_started":
        from .combat import CombatState
        state.combat = CombatState(district_id=pending["district_id"],
                                   attacker=pending["attacker"],
                                   defender=pending["defender"],
                                   next_is_attacker=not pending.get("first_strike", False))
    elif t == "moved_into":
        _close_moved_into(state, rng, pending)
    elif t == "dog_killed":
        _close_dog_killed(state, pending)
        resume = pending.get("resume", "combat_roll")
        if resume == "combat_roll":
            from .combat import resume_combat_roll
            resume_combat_roll(state, rng)
        elif resume == "explosion":
            from . import resources
            resources.resume_explosion(state, rng, pending)
        elif resume == "event_explosion":
            from . import resources
            resources.resume_event_explosion(state, pending)
    elif t == "combat_ended":
        _process_cleanup_queue(state)
    elif t == "influence_gained":
        from .events import draw_and_resolve_event
        draw_and_resolve_event(state, rng, pending["seat"])
        if pending.get("next") == "combat_end":
            open_combat_ended(state, pending["district_id"])
    elif t == "roll":
        _close_roll(state, rng, pending)


def _apply(state: GameState, rng: Rng, seat: int, action: str, pending: dict) -> None:
    t = pending["trigger"]
    if t == "combat_started":
        pending["first_strike"] = True
    elif t == "moved_into":
        dist = state.districts[pending["to_district"]]
        if action == "no_entry":
            if dist.dogs.get(seat, 0) < 1:
                raise CommandError("Нужен ваш пёс в районе")
            pending["cancelled"] = True
        elif action == "ambush":
            if dist.dogs.get(seat, 0) < 1:
                raise CommandError("Нужен ваш пёс в районе")
            pending["ambush_seat"] = seat
        elif action == "detonate":
            if not any(e.get("owner") == seat and e.get("active") for e in dist.explosives):
                raise CommandError("Нужна ваша активная взрывчатка")
            pending["detonate_seat"] = seat
    elif t == "dog_killed":
        pending["saved"] = True
    elif t == "combat_ended":
        state.players[seat].money += 500
    elif t == "influence_gained":
        diff = state.players[pending["seat"]].victory_points - state.players[seat].victory_points
        state.players[seat].money += max(0, diff) * 300
    elif t == "roll":
        pending["rerolled"] = True


def _close_moved_into(state: GameState, rng: Rng, pending: dict) -> None:
    from . import board, resources
    from .combat import start_combat
    if pending.get("cancelled"):
        # «Проход запрещён»: игрок выбирает другой соседний район или остаётся
        state.pending_move_choice = {
            "seat": pending["mover"], "from_district": pending["from_district"],
            "dogs_count": pending["dogs_count"], "mangy_count": pending["mangy_count"],
            "excluded_to": pending["to_district"],
        }
    else:
        board.move(state, pending["mover"], pending["from_district"], pending["to_district"],
                   pending["dogs_count"], pending["mangy_count"])
    if pending.get("ambush_seat") is not None:
        start_combat(state, pending["ambush_seat"], pending["to_district"], pending["mover"])
    if pending.get("detonate_seat") is not None:
        resources.explode(state, rng, pending["to_district"], pending["detonate_seat"])


def resolve_move_choice(state: GameState, seat: int, to_district: int | None) -> None:
    """Завершить выбор после «Проход запрещён» (None — остаться)."""
    pc = state.pending_move_choice
    if pc is None or pc["seat"] != seat:
        raise CommandError("Нет выбора перемещения")
    if to_district is not None:
        if to_district == pc["excluded_to"]:
            raise CommandError("В этот район вход запрещён")
        from . import board
        board.move(state, seat, pc["from_district"], to_district,
                   pc["dogs_count"], pc["mangy_count"])
    state.pending_move_choice = None


def _close_roll(state: GameState, rng: Rng, pending: dict) -> None:
    """Если был сыгран «Перебросить кубик» — перебросить соответствующий кубик."""
    if not pending.get("rerolled"):
        return
    kind = pending.get("kind")
    if kind == "combat":
        c = state.combat
        if c is not None and c.pending is not None:
            face = rng.roll(6)
            c.pending = {"face": face, "opposite": OPPOSITE_FACE[face]}
    elif kind == "authority":
        pk = state.pending_kompromat
        if pk is not None and "face" in pk:
            pk["face"] = rng.roll(6)
    elif kind == "explosion":
        from . import tokens
        pe = state.pending_event_explosion
        if pe is not None and pe["value"] is not None:
            seat = pe["queue"][pe["idx"]]
            pe["value"] = tokens.authority_check(state, rng, seat)
    elif kind == "event":
        from . import tokens
        pe = state.pending_event_roll
        if pe is not None and pe["rolled"]:
            current = pe["order"][pe["idx"]]
            face = rng.roll(6)
            if pe["slug"] == "russkaya_ruletka":
                pe["results"][str(current)] = face
                pe.setdefault("rewards", {})[str(current)] = False
            else:
                pe["results"][str(current)] = tokens.authority_value(state, current, face)
                pe.setdefault("rewards", {})[str(current)] = tokens.is_white_face(state, current, face)
    elif kind == "kazino":
        from . import tokens
        pk = state.pending_kazino
        if pk is not None and pk["rolled"]:
            current = pk["order"][pk["idx"]]
            pk["results"][str(current)] = tokens.authority_check(state, rng, current)


def _close_dog_killed(state: GameState, pending: dict) -> None:
    if pending.get("saved"):
        return
    d = state.districts[pending["district_id"]]
    seat = pending["seat"]
    d.dogs[seat] -= 1
    if d.dogs[seat] <= 0:
        del d.dogs[seat]