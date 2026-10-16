"""Здания и районы: контроль, постройка, разрушение, доход, свойства.

Операции стандартного действия «Сломать / Построить» (постройка и снос),
а также доход и свойства районов (используются при розыгрыше карты в Ч1.9).
"""
from . import board, tokens
from .errors import CommandError
from .rng import Rng
from .state import GameState


def controller(state: GameState, district_id: int) -> int | None:
    """Кто контролирует район (seat) или None (шелудивые/ничья/пусто).

    Контроль: твоих фишек (псы + здание) строго больше, чем у каждого
    другого игрока И чем шелудивых.
    """
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    vals = {}
    for seat in range(state.player_count):
        vals[seat] = d.dogs.get(seat, 0) + (1 if d.building_owner == seat else 0)
    top = max(list(vals.values()) + [d.mangy])
    if top == 0:
        return None
    holders = [seat for seat, v in vals.items() if v == top]
    if len(holders) != 1 or d.mangy == top:
        return None
    return holders[0]


def build(state: GameState, seat: int, district_id: int) -> None:
    """Построить здание (нужен контроль и отсутствие чужого здания)."""
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    if d.building_owner is not None:
        raise CommandError("В районе уже есть здание")
    if controller(state, district_id) != seat:
        raise CommandError("Вы не контролируете район")
    if state.players[seat].money < d.build_cost:
        raise CommandError("Недостаточно денег на постройку")
    state.players[seat].money -= d.build_cost
    d.building_owner = seat


def destroy_building(state: GameState, rng: Rng, seat: int, district_id: int) -> None:
    """Разрушить чужое здание: контроль + взрывчатка; владельцу — страховка."""
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    owner = d.building_owner
    if owner is None:
        raise CommandError("В районе нет здания")
    if owner == seat:
        raise CommandError("Нельзя разрушить своё здание")
    if controller(state, district_id) != seat:
        raise CommandError("Вы не контролируете район")
    if state.players[seat].explosives < 1:
        raise CommandError("Нужна взрывчатка")
    state.players[seat].explosives -= 1
    insurance = d.build_cost // 2 + tokens.authority_check(state, rng, owner) * 100
    state.players[owner].money += insurance
    d.building_owner = None
    from . import reactions
    reactions.open_combat_ended(state, district_id)


def collect_income(state: GameState, seat: int) -> int:
    """Доход со всех районов, где стоит ваше здание. Возвращает сумму."""
    total = 0
    for d in state.districts.values():
        if d.building_owner == seat:
            total += d.income
    state.players[seat].money += total
    return total


def use_ability(state: GameState, rng: Rng, seat: int, district_id: int, target_seat: int | None = None, buy_discard: bool = False, target_district: int | None = None) -> None:
    """Использовать свойство своего здания (раз в ход)."""
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    if d.building_owner != seat:
        raise CommandError("Это не ваше здание")
    if district_id in state.players[seat].used_abilities:
        raise CommandError("Свойство уже использовано в этот ход")
    ability = d.ability
    if not ability:
        raise CommandError("У этого района нет свойства")
    kind = ability.get("kind")
    p = state.players[seat]

    if kind == "spawn_mangy":  # Спальный
        cost = ability.get("cost", 200)
        if p.money < cost:
            raise CommandError("Недостаточно денег")
        target = target_district if target_district is not None else district_id
        if target != district_id and target not in board.neighbors(state, district_id):
            e = board.edge_between(state, district_id, target)
            if e is not None and e["kind"] == "river" and board.is_broken(state, district_id, target):
                raise CommandError("Мост между районами разрушен")
            raise CommandError("Шелудивого можно добавить в этот или соседний район")
        p.money -= cost
        state.districts[target].mangy += 1
    elif kind == "spawn_dog":  # Отделение милиции
        cost = ability.get("cost", 300)
        if p.money < cost:
            raise CommandError("Недостаточно денег")
        p.money -= cost
        d.dogs[seat] = d.dogs.get(seat, 0) + 1
    elif kind == "buy_explosive_or_discard":  # Логово
        if buy_discard:
            cost = ability.get("discard_cost", 1000)
            if p.money < cost:
                raise CommandError("Недостаточно денег")
            if not state.action_deck.discard:
                raise CommandError("Колода сброса пуста")
            p.money -= cost
            p.hand.append(state.action_deck.discard.pop())
        else:
            cost = ability.get("explosive_cost", 600)
            if p.money < cost:
                raise CommandError("Недостаточно денег")
            p.money -= cost
            p.explosives += 1
    elif kind == "buy_kompromat":  # Управа
        if target_seat is None:
            raise CommandError("Укажите, на кого купить компромат")
        cost = ability.get("cost", 800)
        if p.money < cost:
            raise CommandError("Недостаточно денег")
        p.money -= cost
        p.kompromat.append(target_seat)
    elif kind == "peek_events":  # Радиостанция: посмотреть 2 верхние карты событий
        draw = state.event_deck.draw
        if not draw:
            raise CommandError("Колода событий пуста")
        cards = []
        for _ in range(2):
            if draw:
                cards.append(draw.pop())
        state.pending_peek = {"seat": seat, "cards": cards, "district_id": district_id}
        return  # used_abilities пометится в ResolvePeekCommand
    else:
        raise CommandError("Неизвестное свойство района")

    p.used_abilities.append(district_id)