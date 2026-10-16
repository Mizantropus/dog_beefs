"""Эффекты жетонов авторитета (применяются при розыгрыше компромата).

Эффект выпавшего жетона применяется немедленно после броска кубика авторитета,
в дополнение к доходу со всех районов с недвижимостью (collect_income).
"""
from . import board
from .errors import CommandError
from .rng import Rng
from .state import GameState


def apply_effect(state: GameState, rng: Rng, seat: int, effect: str,
                 district_id: int | None = None, card_id: str | None = None,
                 move_to: int | None = None) -> None:
    p = state.players[seat]
    if effect == "dummy":
        return
    if effect == "place_money":
        state.pending_place = {"seat": seat, "kind": "place_money"}
    elif effect == "place_explosive":
        state.pending_place = {"seat": seat, "kind": "place_explosive"}
    elif effect == "take_money":
        p.money += 200
    elif effect == "take_explosive":
        p.explosives += 1
    elif effect == "move":
        state.pending_move = {"seat": seat}
    elif effect == "take_resource":
        state.pending_place = {"seat": seat, "kind": "take_resource"}
    elif effect == "swap_card":
        _queue_choice(state, seat, 2, swap=True, token_top=1)
    elif effect == "swap_card_better":
        _queue_choice(state, seat, None, swap=True, token_top=2)
    elif effect == "take_discard":
        _queue_choice(state, seat, 2, swap=False)


def _queue_choice(state: GameState, seat: int, top: int | None, swap: bool, token_top: int | None = None) -> None:
    """Поставить выбор карты из сброса (top=None — весь сброс, top=2 — две верхние)."""
    discard = state.action_deck.discard
    if not discard:
        return
    pool = discard if top is None else discard[-top:]
    state.pending_swap = {"seat": seat, "pool": list(pool), "swap": swap, "token_top": token_top}


def resolve_place(state: GameState, seat: int, district_id: int | None, resource: str | None = None) -> None:
    """Завершить выбор района для «Положить 200$/взрывчатку» или «Забрать ресурс»."""
    pc = state.pending_place
    if pc is None or pc["seat"] != seat:
        raise CommandError("Нет выбора района")
    kind = pc["kind"]
    if kind == "take_resource" and resource == "none":
        state.players[seat].money += 300
        state.pending_place = None
        return
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    if kind == "place_money":
        if d.dogs.get(seat, 0) < 1:
            raise CommandError("Нужен ваш пёс в районе")
        d.money += 200
    elif kind == "place_explosive":
        if d.dogs.get(seat, 0) < 1:
            raise CommandError("Нужен ваш пёс в районе")
        d.explosives.append({"owner": seat, "active": False})
    elif kind == "take_resource":
        if d.dogs.get(seat, 0) < 1 and d.building_owner != seat:
            raise CommandError("Нужны ваши фишки в районе")
        _do_take_resource(state, seat, d, resource)
    state.pending_place = None


def resolve_move(state: GameState, seat: int, from_d: int, to_d: int,
                 dogs_count: int = 0, mangy_count: int = 0) -> None:
    """Завершить «Перемещение» (жетон авторитета)."""
    if state.pending_move is None or state.pending_move["seat"] != seat:
        raise CommandError("Нет перемещения")
    board.move(state, seat, from_d, to_d, dogs_count, mangy_count)
    state.pending_move = None


def resolve_swap_token(state: GameState, rng: Rng, seat: int) -> None:
    """Начать обмен жетона влияния (вместо обмена карты)."""
    ps = state.pending_swap
    if ps is None or ps["seat"] != seat or ps.get("token_top") is None:
        raise CommandError("Нет обмена жетона")
    drawn, rest = rng.draw_bag(state.influence_bag, ps["token_top"])
    state.influence_bag = rest
    state.pending_swap = None
    if drawn:
        state.pending_token_swap = {"seat": seat, "drawn": drawn}


def resolve_token_swap(state: GameState, seat: int, line: str, slot: int, chosen_index: int = 0) -> None:
    """Завершить обмен жетона влияния: заменить слот на выбранный жетон из мешка."""
    pts = state.pending_token_swap
    if pts is None or pts["seat"] != seat:
        raise CommandError("Нет обмена жетона")
    if line not in ("authority", "combat"):
        raise CommandError("Неверная линия")
    if not (0 <= slot <= 5):
        raise CommandError("Неверный слот")
    drawn = pts["drawn"]
    if chosen_index < 0 or chosen_index >= len(drawn):
        raise CommandError("Неверный выбор")
    new_token = drawn[chosen_index]
    for i, t in enumerate(drawn):
        if i != chosen_index:
            state.influence_bag.append(t)
    p = state.players[seat]
    if line == "authority":
        p.authority_line[slot] = new_token
    else:
        p.combat_line[slot] = new_token
    state.pending_token_swap = None


def _do_take_resource(state: GameState, seat: int, d, resource: str | None) -> None:
    """Забрать выбранный ресурс из района (или 300$ из банка)."""
    p = state.players[seat]
    if resource == "money":
        if d.money <= 0:
            raise CommandError("В районе нет денег")
        p.money += d.money
        d.money = 0
    elif resource == "explosive":
        for ex in list(d.explosives):
            if not ex["active"]:
                d.explosives.remove(ex)
                p.explosives += 1
                return
        for ex in list(d.explosives):
            if ex["owner"] == seat:
                d.explosives.remove(ex)
                p.explosives += 1
                return
        raise CommandError("Нет взрывчатки, которую можно просто забрать")
    elif resource == "kompromat":
        if d.kompromat:
            t = d.kompromat[0]
            d.kompromat.remove(t)
            p.kompromat.append(t)
        else:
            raise CommandError("В районе нет компромата")
    elif resource == "none":
        p.money += 300
    else:
        raise CommandError("Укажите ресурс")


def _district_with_dogs(state: GameState, seat: int, district_id: int | None):
    if district_id is not None:
        d = state.districts.get(district_id)
        if d is not None and d.dogs.get(seat, 0) >= 1:
            return d
    for d in state.districts.values():
        if d.dogs.get(seat, 0) >= 1:
            return d
    return None


def _district_with_pieces(state: GameState, seat: int, district_id: int | None):
    if district_id is not None:
        d = state.districts.get(district_id)
        if d is not None and (d.dogs.get(seat, 0) >= 1 or d.building_owner == seat):
            return d
    for d in state.districts.values():
        if d.dogs.get(seat, 0) >= 1 or d.building_owner == seat:
            return d
    return None


def _take_resource(state: GameState, seat: int, district_id: int | None) -> None:
    """Забрать любой ресурс из района со своими фишками; нечего — 300$ из банка."""
    d = _district_with_pieces(state, seat, district_id)
    if d is not None:
        if d.money > 0:
            state.players[seat].money += d.money
            d.money = 0
            return
        if seat in d.kompromat:
            d.kompromat.remove(seat)
            state.players[seat].kompromat.append(seat)
            return
        for ex in list(d.explosives):
            if ex["owner"] != seat and not ex["active"]:
                d.explosives.remove(ex)
                state.players[seat].explosives += 1
                return
    state.players[seat].money += 300


def _swap_with_discard(state: GameState, seat: int, card_id: str | None, top: int | None) -> None:
    """Поменять карту из руки на карту из сброса (top=2 — из двух верхних, None — любую)."""
    if card_id is None or card_id not in state.players[seat].hand:
        return
    discard = state.action_deck.discard
    if not discard:
        return
    pool = discard if top is None else discard[-top:]
    taken = pool[-1]  # упрощённо: верхняя из допустимых
    state.action_deck.discard.remove(taken)
    state.players[seat].hand.remove(card_id)
    state.action_deck.discard.append(card_id)
    state.players[seat].hand.append(taken)


def _take_discard(state: GameState, seat: int) -> None:
    """Взять одну из двух верхних карт сброса (упрощённо: верхнюю)."""
    if state.action_deck.discard:
        state.players[seat].hand.append(state.action_deck.discard.pop())