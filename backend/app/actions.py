"""Стандартные действия (розыгрыш карты).

resolve_standard — диспетчер: по standard_key карты и выбранному поддействию
выполняет нужную операцию (resources / buildings / combat).
"""
from . import board, influence, reactions, resources
from .buildings import build, collect_income, destroy_building
from .combat import start_combat, validate_start
from .errors import CommandError
from .rng import Rng
from .state import GameState


def add_mangy(state: GameState, seat: int, district_id: int) -> None:
    """Добавить шелудивого в район, где есть ваши псы или здание."""
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    if d.dogs.get(seat, 0) < 1 and d.building_owner != seat:
        raise CommandError("Нужен ваш пёс или здание в районе")
    d.mangy += 1


def recruit_mangy(state: GameState, seat: int, district_id: int) -> None:
    """Завербовать шелудивого (превратить в вашего пса)."""
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    if d.mangy < 1:
        raise CommandError("В районе нет шелудивых")
    if d.dogs.get(seat, 0) < 1 and d.building_owner != seat:
        raise CommandError("Нужен ваш пёс или здание в районе")
    d.mangy -= 1
    d.dogs[seat] = d.dogs.get(seat, 0) + 1


def resolve_standard(state: GameState, rng: Rng, seat: int, standard_key: str,
                     option: str | None = None, district_id: int | None = None,
                     amount: int | None = None, target_seat: int | None = None,
                     defender: int | None = None, active: bool = False,
                     resource: str | None = None, to_district: int | None = None,
                     dogs_count: int | None = None, mangy_count: int | None = None) -> None:
    """Выполнить стандартное действие карты."""
    if standard_key == "lift_place":
        if option == "take_resource":
            if resource == "money":
                resources.take_money(state, seat, district_id)
            elif resource == "kompromat":
                resources.take_kompromat_other(state, seat, district_id, target_seat)
            elif resource == "explosive":
                resources.take_explosive(state, seat, district_id)
            else:
                raise CommandError("Укажите ресурс")
        elif option == "place_resource":
            if resource == "money":
                resources.place_money(state, seat, district_id, amount or 0)
            elif resource == "kompromat":
                resources.place_kompromat(state, seat, district_id, target_seat)
            elif resource == "explosive":
                resources.mine(state, seat, district_id, active=False)
            else:
                raise CommandError("Укажите ресурс")
        elif option == "lift_kompromat":
            resources.lift_kompromat_self(state, rng, seat, district_id)
        elif option == "mine":
            resources.mine(state, seat, district_id, active=True)
        elif option == "demine":
            resources.demine(state, rng, seat, district_id)
        else:
            raise CommandError("Неизвестное поддействие")
    elif standard_key == "summon_recruit":
        if option == "add_mangy":
            add_mangy(state, seat, district_id)
        elif option == "recruit_mangy":
            recruit_mangy(state, seat, district_id)
        else:
            raise CommandError("Неизвестное поддействие")
    elif standard_key == "move":
        board.move(state, seat, district_id, to_district, dogs_count or 0, mangy_count or 0)
    elif standard_key == "start_fight":
        validate_start(state, seat, district_id, defender)
        if reactions.open_combat_started(state, seat, defender, district_id):
            return  # окно first_strike
        start_combat(state, seat, district_id, defender)
    elif standard_key == "build_destroy":
        if option == "build":
            build(state, seat, district_id)
            influence.influence_for_build(state, seat, district_id)
        elif option == "destroy_building":
            destroy_building(state, rng, seat, district_id)
            influence.influence_for_destroy(state, seat, district_id)
        elif option == "destroy_bridge":
            board.destroy_bridge(state, seat, district_id, to_district)
        elif option == "repair_bridge":
            board.repair_bridge(state, seat, district_id, to_district)
        else:
            raise CommandError("Неизвестное поддействие")
    else:
        raise CommandError("Неизвестное действие")