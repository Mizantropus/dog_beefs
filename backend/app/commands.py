"""Команды (намерения игроков).

Движок (engine.py) выполняет цикл:
    загрузить -> validate -> apply -> version+1 / rng_state -> сохранить.

В apply работать с ПЕРЕДАННОЙ копией состояния, НЕ трогать version и rng_state.
"""
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from . import authority, board, events, reactions, resources, tokens
from .actions import resolve_standard
from .buildings import collect_income, use_ability
from .combat import ack_combat_result, ack_mangy_roll, resolve_roll, roll_combat, start_combat, validate_start
from .errors import CommandError  # реэкспорт для совместимости импортов
from .influence import check_win
from .rng import Rng
from .round import advance_draft, end_round, next_turn
from .state import GameState, Phase


class Command(BaseModel):
    """Базовый класс команды."""

    seat: int  # кто отдаёт команду

    def validate(self, state: GameState) -> None:
        raise NotImplementedError

    def apply(self, state: GameState, rng: Rng) -> GameState:
        raise NotImplementedError


class PassCommand(Command):
    """Пас в фазе розыгрыша: пропустить ход без дохода и передать ход следующему."""

    type: Literal["pass"] = "pass"

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Пас доступен только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if state.players[self.seat].has_played:
            raise CommandError("Вы уже сделали ход")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        state.passes_in_a_row += 1
        state.players[self.seat].has_played = True
        if state.passes_in_a_row >= state.player_count:
            end_round(state, rng)
        else:
            next_turn(state)
        return state


class EndTurnCommand(Command):
    """Завершить ход: передать ход следующему игроку (после карты и свойств)."""

    type: Literal["end_turn"] = "end_turn"

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Завершение хода доступно только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if state.combat is not None:
            raise CommandError("Сначала завершите бой")
        if state.pending_kompromat is not None:
            raise CommandError("Сначала разрешите бросок компромата")
        if state.pending_swap is not None:
            raise CommandError("Сначала завершите обмен карты")
        if state.pending_event is not None:
            raise CommandError("Сначала подтвердите карту события")
        if state.pending_event_roll is not None:
            raise CommandError("Сначала завершите бросок события")
        if state.pending_may_event is not None:
            raise CommandError("Сначала завершите событие")
        if state.pending_kazino is not None:
            raise CommandError("Сначала завершите казино")
        if state.pending_choice is not None:
            raise CommandError("Сначала сделайте выбор")
        if state.pending_place is not None:
            raise CommandError("Сначала завершите выбор района")
        if state.pending_move is not None:
            raise CommandError("Сначала завершите перемещение")
        if state.pending_token_swap is not None:
            raise CommandError("Сначала завершите обмен жетона")
        if state.pending_move_choice is not None:
            raise CommandError("Сначала выберите район после «Проход запрещён»")
        if state.pending_event_explosion is not None:
            raise CommandError("Сначала завершите взрыв")
        if state.pending_discard_buy is not None:
            raise CommandError("Сначала выберите карту из сброса")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if state.passes_in_a_row >= state.player_count:
            end_round(state, rng)
        else:
            next_turn(state)
        return state


class DiscardCardCommand(Command):
    """Сбросить карту действия и получить 100$ (без дохода и свойств зданий)."""

    type: Literal["discard_card"] = "discard_card"
    card_id: str

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Карты сбрасываются только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if state.combat is not None:
            raise CommandError("Сначала завершите бой")
        if state.players[self.seat].has_played:
            raise CommandError("Вы уже сделали ход")
        if self.card_id not in state.players[self.seat].hand:
            raise CommandError("Нет такой карты на руке")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        p = state.players[self.seat]
        p.hand.remove(self.card_id)
        state.action_deck.discard.append(self.card_id)
        p.money += 100
        p.has_played = True
        state.passes_in_a_row = 0
        return state


class PickDraftCardCommand(Command):
    """Выбор карты в драфте."""

    type: Literal["pick_draft"] = "pick_draft"
    card_id: str

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.DRAFT or state.draft is None:
            raise CommandError("Сейчас не фаза драфта")
        if not (0 <= self.seat < state.player_count):
            raise CommandError("Неверный игрок")
        if self.seat in state.draft.picked:
            raise CommandError("Вы уже выбрали карту в этом подраунде")
        if self.card_id not in state.draft.hand.get(self.seat, []):
            raise CommandError("Этой карты нет в вашем драфте")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        d = state.draft
        d.hand[self.seat].remove(self.card_id)
        state.players[self.seat].hand.append(self.card_id)
        d.picked.append(self.seat)
        if len(d.picked) == state.player_count:
            advance_draft(state, rng)
        return state


class PlayCardCommand(Command):
    """Сыграть карту действия: стандартное действие + доход + сброс карты."""

    type: Literal["play_card"] = "play_card"
    card_id: str
    option: str | None = None
    district_id: int | None = None
    amount: int | None = None
    target_seat: int | None = None
    defender: int | None = None
    active: bool = False
    resource: str | None = None
    to_district: int | None = None    # для move / мостов
    dogs_count: int | None = None     # для move
    mangy_count: int | None = None    # для move

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Карты играются только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if state.combat is not None:
            raise CommandError("Сначала завершите бой")
        if state.players[self.seat].has_played:
            raise CommandError("Вы уже сделали ход")
        if self.card_id not in state.players[self.seat].hand:
            raise CommandError("Нет такой карты на руке")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        p = state.players[self.seat]
        p.has_played = True
        p.played_standard = True
        vp_before = p.victory_points
        card = state.cards[self.card_id]

        # перемещение — особый случай (окно реакции на вход)
        if card["standard_key"] == "move":
            board.validate_move(state, self.seat, self.district_id, self.to_district,
                                self.dogs_count or 0, self.mangy_count or 0)
            collect_income(state, self.seat)
            p.hand.remove(self.card_id)
            state.action_deck.discard.append(self.card_id)
            check_win(state)
            state.passes_in_a_row = 0
            if reactions.open_moved_into(state, self.seat, self.district_id, self.to_district,
                                         self.dogs_count or 0, self.mangy_count or 0):
                return state  # close -> move + next_turn
            board.move(state, self.seat, self.district_id, self.to_district,
                       self.dogs_count or 0, self.mangy_count or 0)
            return state

        resolve_standard(state, rng, self.seat, card["standard_key"], self.option,
                         district_id=self.district_id, amount=self.amount,
                         target_seat=self.target_seat, defender=self.defender,
                         active=self.active, resource=self.resource,
                         to_district=self.to_district, dogs_count=self.dogs_count,
                         mangy_count=self.mangy_count)
        # старт боя мог открыть окно first_strike
        if state.pending_reaction is not None:
            collect_income(state, self.seat)
            p.hand.remove(self.card_id)
            state.action_deck.discard.append(self.card_id)
            check_win(state)
            state.passes_in_a_row = 0
            return state  # ход ждёт боя

        collect_income(state, self.seat)
        p.hand.remove(self.card_id)
        state.action_deck.discard.append(self.card_id)
        check_win(state)
        state.passes_in_a_row = 0
        # получено влияние -> окно субсидии + событие
        if state.phase != Phase.FINISHED and p.victory_points > vp_before:
            if reactions.open_influence_gained(state, self.seat):
                return state  # close -> событие
            events.draw_and_resolve_event(state, rng, self.seat)
            check_win(state)
        return state


class PlayKompromatCommand(Command):
    """Сыграть компромат: сброс + бросок авторитета + доход + эффект жетона."""

    type: Literal["play_kompromat"] = "play_kompromat"
    district_id: int | None = None      # для эффектов с выбором района
    card_id: str | None = None          # для эффектов с выбором карты
    move_to: int | None = None          # для эффекта «Перемещение»
    property_district: int | None = None  # белый жетон -> свойство района
    target_seat: int | None = None      # для свойства Управы
    buy_discard: bool = False           # для свойств Логова/Завода
    target_district: int | None = None  # для свойства Спального
    discard_target_seat: int | None = None  # какой компромат сбросить (на кого)

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Компромат играется только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if state.combat is not None:
            raise CommandError("Сначала завершите бой")
        if state.players[self.seat].has_played:
            raise CommandError("Вы уже сделали ход")
        if not state.players[self.seat].kompromat:
            raise CommandError("У вас нет компромата")
        if self.discard_target_seat is not None and self.discard_target_seat not in state.players[self.seat].kompromat:
            raise CommandError("Нет такого компромата")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.discard_target_seat is not None:
            state.players[self.seat].kompromat.remove(self.discard_target_seat)
        else:
            state.players[self.seat].kompromat.pop()
        face = rng.roll(6)
        state.players[self.seat].has_played = True
        state.pending_kompromat = {"seat": self.seat, "face": face}
        reactions.open_roll(state, self.seat, "authority")
        return state


class ChooseInfluenceTokenCommand(Command):
    """Решить, куда положить вытянутый жетон влияния: в слот линии или сразу ПО."""

    type: Literal["choose_influence"] = "choose_influence"
    swap_slot: int | None = None  # индекс 0..5 в линии жетона; None -> сразу ПО

    def validate(self, state: GameState) -> None:
        entry = next((e for e in state.pending_influence if e["seat"] == self.seat), None)
        if entry is None:
            raise CommandError("Нет неразрешённого жетона влияния")
        if self.swap_slot is not None and not (0 <= self.swap_slot <= 5):
            raise CommandError("Слот должен быть 0..5")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        entry = next((e for e in state.pending_influence if e["seat"] == self.seat), None)
        token = entry["token"]
        if self.swap_slot is not None:
            if tokens.is_combat_token(token):
                state.players[self.seat].combat_line[self.swap_slot] = token
            else:
                state.players[self.seat].authority_line[self.swap_slot] = token
        state.pending_influence.remove(entry)
        return state


class UseAbilityCommand(Command):
    """Использовать свойство своего здания (раз в ход)."""

    type: Literal["use_ability"] = "use_ability"
    district_id: int
    target_seat: int | None = None   # для Управы
    buy_discard: bool = False        # для Логова: купить верхнюю карту сброса
    target_district: int | None = None  # для Спального: соседний район

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Свойства используются только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if state.combat is not None:
            raise CommandError("Сначала завершите бой")
        if not state.players[self.seat].played_standard:
            raise CommandError("Сначала разыграйте стандартное действие (карту)")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        use_ability(state, rng, self.seat, self.district_id,
                    target_seat=self.target_seat, buy_discard=self.buy_discard,
                    target_district=self.target_district)
        return state


class PlaySituationalCommand(Command):
    """Сыграть ситуативное действие в ответ на триггер."""

    type: Literal["play_situational"] = "play_situational"
    action: str                     # ключ ситуативного действия
    card_id: str | None = None      # какую карту сбросить; None -> компромат
    target_seat: int | None = None  # какой компромат сбросить (если card_id=None)

    def validate(self, state: GameState) -> None:
        pending = state.pending_reaction
        if pending is None:
            raise CommandError("Нет ожидающей реакции")
        if self.action not in reactions.TRIGGER_ACTIONS[pending["trigger"]]:
            raise CommandError("Это действие не подходит под текущую ситуацию")
        if self.seat not in reactions.eligible(state, pending):
            raise CommandError("Вы не можете ответить сейчас")
        if self.seat in pending["responded"]:
            raise CommandError("Вы уже ответили")
        if self.card_id is not None:
            if self.card_id not in state.players[self.seat].hand:
                raise CommandError("Нет такой карты на руке")
            if self.action not in reactions.card_actions(state.cards[self.card_id]):
                raise CommandError("Не то действие на карте")
        else:
            if not reactions.has_situational(state, self.seat, self.action):
                raise CommandError("Нет карты с этим действием")
            if self.target_seat is not None:
                if self.target_seat not in state.players[self.seat].kompromat:
                    raise CommandError("Нет такого компромата")
            elif not state.players[self.seat].kompromat:
                raise CommandError("Нет компромата")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.card_id is not None:
            state.players[self.seat].hand.remove(self.card_id)
            state.action_deck.discard.append(self.card_id)
        else:
            if self.target_seat is not None:
                state.players[self.seat].kompromat.remove(self.target_seat)
            else:
                state.players[self.seat].kompromat.pop()
        reactions.play(state, rng, self.seat, self.action)
        return state


class PassReactionCommand(Command):
    """Пропустить окно реакции."""

    type: Literal["pass_reaction"] = "pass_reaction"

    def validate(self, state: GameState) -> None:
        pending = state.pending_reaction
        if pending is None:
            raise CommandError("Нет ожидающей реакции")
        if self.seat not in reactions.eligible(state, pending):
            raise CommandError("Вы не можете ответить сейчас")
        if self.seat in pending["responded"]:
            raise CommandError("Вы уже ответили")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        reactions.pass_reaction(state, rng, self.seat)
        return state


class StartCombatCommand(Command):
    """Начать бой (стандартное действие «Начать бой»)."""

    type: Literal["start_combat"] = "start_combat"
    district_id: int
    defender: int | None = None

    def validate(self, state: GameState) -> None:
        if state.phase != Phase.PLAY:
            raise CommandError("Бой доступен только в фазе розыгрыша")
        if state.current_seat != self.seat:
            raise CommandError("Сейчас не ваш ход")
        validate_start(state, self.seat, self.district_id, self.defender)

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if reactions.open_combat_started(state, self.seat, self.defender, self.district_id):
            return state  # окно first_strike; close создаст бой
        start_combat(state, self.seat, self.district_id, self.defender)
        state.passes_in_a_row = 0
        return state


class RollCombatDieCommand(Command):
    """Бросок текущей стороны в бою."""

    type: Literal["roll_combat"] = "roll_combat"

    def validate(self, state: GameState) -> None:
        c = state.combat
        if c is None:
            raise CommandError("Бой не идёт")
        if c.pending is not None:
            raise CommandError("Сначала примените результат прошлого броска")
        roller = c.attacker if c.next_is_attacker else c.defender
        if roller is not None and roller != self.seat:
            raise CommandError("Сейчас не ваш бросок")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        roll_combat(state, rng)
        return state


class ResolveCombatRollCommand(Command):
    """Применить бросок боевого кубика (flip=True — перевернуть за компромат)."""

    type: Literal["resolve_combat"] = "resolve_combat"
    flip: bool = False
    reroll: bool = False
    move_seat: int | None = None   # для move_dog: чей пёс (None = шелудивый)
    move_to: int | None = None     # для move_dog: соседний район

    def validate(self, state: GameState) -> None:
        c = state.combat
        if c is None or c.pending is None:
            raise CommandError("Нет ожидающего броска")
        roller = c.attacker if c.next_is_attacker else c.defender
        if roller != self.seat:
            raise CommandError("Сейчас не ваш бросок")
        if self.reroll and not reactions.has_situational(state, self.seat, "reroll"):
            raise CommandError("Нет карты «Перебросить кубик»")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.reroll:
            reactions.spend_situational(state, self.seat, "reroll")
            roll_combat(state, rng)
            return state
        resolve_roll(state, rng, self.flip, move_seat=self.move_seat, move_to=self.move_to)
        return state


class ResolveKompromatCommand(Command):
    """Разрешить бросок компромата: переброс / принять эффект / выбор свойства (белый жетон)."""

    type: Literal["resolve_kompromat"] = "resolve_kompromat"
    reroll: bool = False
    district_id: int | None = None      # для эффекта или для свойства района (белый жетон)
    target_seat: int | None = None
    buy_discard: bool = False
    target_district: int | None = None

    def validate(self, state: GameState) -> None:
        pending = state.pending_kompromat
        if pending is None or pending["seat"] != self.seat:
            raise CommandError("Нет ожидающего броска компромата")
        if self.district_id is not None and self.district_id not in state.districts:
            raise CommandError("Такого района нет")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        pending = state.pending_kompromat
        if self.reroll:
            pending["face"] = rng.roll(6)
            return state
        if pending.get("kind") == "lift_kompromat":
            value = tokens.authority_value(state, self.seat, pending["face"])
            d = state.districts[pending["district_id"]]
            if value >= 5 and self.seat in d.kompromat:
                d.kompromat.remove(self.seat)
                state.players[self.seat].kompromat.append(self.seat)
            state.pending_kompromat = None
            state.passes_in_a_row = 0
            return state
        if pending.get("choose"):
            # белый жетон: использовать свойство района (district_id=None -> пропустить)
            if self.district_id is not None:
                use_ability(state, rng, self.seat, self.district_id,
                            target_seat=self.target_seat, buy_discard=self.buy_discard,
                            target_district=self.target_district)
            state.pending_kompromat = None
            state.passes_in_a_row = 0
            return state
        # принять бросок: доход + эффект жетона авторитета
        face = pending["face"]
        token_key = state.players[self.seat].authority_line[face]
        effect = tokens.AUTHORITY_TOKENS[token_key]["effect"]
        collect_income(state, self.seat)
        authority.apply_effect(state, rng, self.seat, effect, self.district_id, None, None)
        if tokens.is_white_face(state, self.seat, face):
            state.pending_kompromat = {"seat": self.seat, "choose": True}
            return state
        state.pending_kompromat = None
        state.passes_in_a_row = 0
        return state


class ResolvePeekCommand(Command):
    """Радиостанция: сбросить одну из просмотренных карт событий (300$) или вернуть обе."""

    type: Literal["resolve_peek"] = "resolve_peek"
    discard_index: int | None = None    # 0/1 — какую сбросить; None — вернуть обе

    def validate(self, state: GameState) -> None:
        if state.pending_peek is None or state.pending_peek["seat"] != self.seat:
            raise CommandError("Нет ожидающего просмотра событий")
        if self.discard_index is not None and self.discard_index not in (0, 1):
            raise CommandError("Неверный индекс сброса")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        pending = state.pending_peek
        cards = pending["cards"]
        if self.discard_index is not None:
            if self.discard_index >= len(cards):
                raise CommandError("Неверный индекс сброса")
            p = state.players[self.seat]
            if p.money < 300:
                raise CommandError("Недостаточно денег (нужно 300$)")
            p.money -= 300
            for i, c in enumerate(cards):
                if i == self.discard_index:
                    state.event_deck.discard.append(c)
                else:
                    state.event_deck.draw.append(c)
        else:
            for c in reversed(cards):
                state.event_deck.draw.append(c)
        state.players[self.seat].used_abilities.append(pending["district_id"])
        state.pending_peek = None
        return state


class PickDiscardBuyCommand(Command):
    """Логово: выбрать одну из двух купленных карт сброса (вторая вернётся наверх)."""

    type: Literal["pick_discard_buy"] = "pick_discard_buy"
    card_id: str

    def validate(self, state: GameState) -> None:
        pdb = state.pending_discard_buy
        if pdb is None or pdb["seat"] != self.seat:
            raise CommandError("Нет выбора карты из сброса")
        if self.card_id not in pdb["cards"]:
            raise CommandError("Такой карты нет в выборе")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        pdb = state.pending_discard_buy
        state.pending_discard_buy = None
        for cid in pdb["cards"]:
            if cid == self.card_id:
                state.players[self.seat].hand.append(cid)
            else:
                state.action_deck.discard.append(cid)
        state.players[self.seat].used_abilities.append(pdb["district_id"])
        return state


class ResolveChoiceCommand(Command):
    """Выбор игрока (мост и т.п.)."""

    type: Literal["resolve_choice"] = "resolve_choice"
    value: str | list | int | None = None

    def validate(self, state: GameState) -> None:
        if state.pending_choice is None:
            raise CommandError("Нет ожидающего выбора")
        if state.pending_choice["seat"] != self.seat:
            raise CommandError("Не ваш выбор")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        events.resolve_choice(state, self.value, rng)
        return state


class KazinoCommand(Command):
    """Казино: бросок / переброс / завершение текущего игрока."""

    type: Literal["kazino"] = "kazino"
    action: str = "done"    # "roll" | "reroll" | "done"

    def validate(self, state: GameState) -> None:
        if state.pending_kazino is None:
            raise CommandError("Казино не идёт")
        if self.action not in ("roll", "reroll", "done"):
            raise CommandError("Неизвестное действие")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.action == "done":
            events.kazino_done(state, self.seat)
        else:
            events.kazino_roll(state, rng, self.seat, reroll=(self.action == "reroll"))
        return state


class MayEventCommand(Command):
    """Действие/завершение в добровольном событии."""

    type: Literal["may_event"] = "may_event"
    action: str = "done"                 # "act" | "done"
    target_seat: int | None = None
    count: int = 1
    district_id: int | None = None
    resource: str | None = None
    choice: str | None = None

    def validate(self, state: GameState) -> None:
        if state.pending_may_event is None:
            raise CommandError("Нет добровольного события")
        if self.action not in ("act", "done"):
            raise CommandError("Неизвестное действие")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.action == "done":
            events.may_event_done(state, self.seat)
        else:
            events.may_event_act(state, rng, self.seat, target_seat=self.target_seat,
                                 count=self.count, district_id=self.district_id,
                                 resource=self.resource, choice=self.choice)
        return state


class EventExplosionCommand(Command):
    """Взрыв от карты события: бросок авторитета / ОК."""

    type: Literal["event_explosion"] = "event_explosion"
    action: str = "ok"    # "roll" | "ok"

    def validate(self, state: GameState) -> None:
        if state.pending_event_explosion is None:
            raise CommandError("Нет взрыва")
        if self.action not in ("roll", "ok"):
            raise CommandError("Неизвестное действие")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.action == "roll":
            resources.event_explosion_roll(state, rng, self.seat)
        else:
            resources.event_explosion_ok(state, rng, self.seat)
        return state


class ResolveMoveChoiceCommand(Command):
    """Выбор нового района после «Проход запрещён» (None — остаться)."""

    type: Literal["resolve_move_choice"] = "resolve_move_choice"
    to_district: int | None = None

    def validate(self, state: GameState) -> None:
        if state.pending_move_choice is None:
            raise CommandError("Нет выбора перемещения")
        if state.pending_move_choice["seat"] != self.seat:
            raise CommandError("Не ваш выбор")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        reactions.resolve_move_choice(state, self.seat, self.to_district)
        return state


class ResolvePlaceCommand(Command):
    """Выбор района для жетона авторитета (Положить 200$/взрывчатку/Забрать ресурс)."""

    type: Literal["resolve_place"] = "resolve_place"
    district_id: int | None = None
    resource: str | None = None

    def validate(self, state: GameState) -> None:
        if state.pending_place is None:
            raise CommandError("Нет выбора района")
        if state.pending_place["seat"] != self.seat:
            raise CommandError("Не ваш выбор")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        authority.resolve_place(state, self.seat, self.district_id, self.resource)
        return state


class ResolveMoveCommand(Command):
    """Завершить «Перемещение» (жетон авторитета)."""

    type: Literal["resolve_move"] = "resolve_move"
    from_district: int
    to_district: int
    dogs_count: int = 0
    mangy_count: int = 0

    def validate(self, state: GameState) -> None:
        if state.pending_move is None:
            raise CommandError("Нет перемещения")
        if state.pending_move["seat"] != self.seat:
            raise CommandError("Не ваш ход")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        authority.resolve_move(state, self.seat, self.from_district, self.to_district,
                               self.dogs_count, self.mangy_count)
        return state


class ResolveTokenSwapCommand(Command):
    """Завершить обмен жетона влияния."""

    type: Literal["resolve_token_swap"] = "resolve_token_swap"
    line: str
    slot: int
    chosen_index: int = 0

    def validate(self, state: GameState) -> None:
        if state.pending_token_swap is None:
            raise CommandError("Нет обмена жетона")
        if state.pending_token_swap["seat"] != self.seat:
            raise CommandError("Не ваш выбор")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        authority.resolve_token_swap(state, self.seat, self.line, self.slot, self.chosen_index)
        return state


class ResolveSwapCommand(Command):
    """Завершить выбор карты сброса (обмен/взятие или пропуск)."""

    type: Literal["resolve_swap"] = "resolve_swap"
    discard_card_id: str | None = None   # какую карту взять из сброса; None -> пропустить
    hand_card_id: str | None = None      # какую карту отдать (для swap)
    token_swap: bool = False             # вместо карты — обменять жетон влияния

    def validate(self, state: GameState) -> None:
        pending = state.pending_swap
        if pending is None or pending["seat"] != self.seat:
            raise CommandError("Нет ожидающего выбора карты")
        if self.discard_card_id is not None and self.discard_card_id not in pending["pool"]:
            raise CommandError("Этой карты нет среди доступных")
        if pending["swap"] and self.discard_card_id is not None and self.hand_card_id is None:
            raise CommandError("Укажите карту из руки для обмена")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        if self.token_swap:
            authority.resolve_swap_token(state, rng, self.seat)
            return state
        pending = state.pending_swap
        p = state.players[self.seat]
        if self.discard_card_id is not None:
            if pending["swap"]:
                if self.hand_card_id not in p.hand:
                    raise CommandError("Нет такой карты на руке")
                p.hand.remove(self.hand_card_id)
                state.action_deck.discard.append(self.hand_card_id)
                state.action_deck.discard.remove(self.discard_card_id)
                p.hand.append(self.discard_card_id)
            else:
                state.action_deck.discard.remove(self.discard_card_id)
                p.hand.append(self.discard_card_id)
        state.pending_swap = None
        return state


class EventRollCommand(Command):
    """Бросок в пошаговом событии (лотерея, призы, нулевая сумма, рулетка)."""

    type: Literal["event_roll"] = "event_roll"
    action: str = "roll"  # "roll" | "ok"

    def validate(self, state: GameState) -> None:
        pend = state.pending_event_roll
        if pend is None:
            raise CommandError("Нет события с броском")
        if self.action not in ("roll", "ok"):
            raise CommandError("Неизвестное действие")
        current = pend["order"][pend["idx"]]
        if current != self.seat:
            raise CommandError("Сейчас не ваш ход")
        if self.action == "roll" and pend["rolled"]:
            raise CommandError("Вы уже бросили")
        if self.action == "ok" and not pend["rolled"]:
            raise CommandError("Сначала бросьте")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        events.event_roll(state, rng, self.seat, self.action)
        return state


class AckCombatResultCommand(Command):
    """Подтвердить результат боевого жетона (кнопка «ОК»)."""

    type: Literal["ack_combat_result"] = "ack_combat_result"

    def validate(self, state: GameState) -> None:
        if state.pending_combat_result is None:
            raise CommandError("Нет результата боя для подтверждения")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        ack_combat_result(state, rng)
        return state


class AckMangyRollCommand(Command):
    """Подтвердить бросок шелудивых (кнопка «ОК»)."""

    type: Literal["ack_mangy_roll"] = "ack_mangy_roll"

    def validate(self, state: GameState) -> None:
        c = state.combat
        if c is None or c.pending is None or not c.pending.get("mangy"):
            raise CommandError("Нет броска шелудивых для подтверждения")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        ack_mangy_roll(state, rng)
        return state


class AckPenaltyCommand(Command):
    """Подтвердить штрафное условие (кнопка «ОК»)."""

    type: Literal["ack_penalty"] = "ack_penalty"

    def validate(self, state: GameState) -> None:
        if state.pending_penalty is None:
            raise CommandError("Нет штрафа для подтверждения")
        if self.seat in state.pending_penalty["acked"]:
            raise CommandError("Вы уже подтвердили")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        state.pending_penalty["acked"].append(self.seat)
        if len(state.pending_penalty["acked"]) >= state.player_count:
            state.pending_penalty = None
        return state


class AckEventCommand(Command):
    """Подтвердить карту события (кнопка «ОК»)."""

    type: Literal["ack_event"] = "ack_event"

    def validate(self, state: GameState) -> None:
        if state.pending_event is None:
            raise CommandError("Нет карты события для подтверждения")
        if self.seat in state.pending_event["acked"]:
            raise CommandError("Вы уже подтвердили")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        events.ack_event(state, rng, self.seat)
        return state


class AdvancePhaseCommand(Command):
    """Служебная команда: перейти к следующей фазе (для тестов)."""

    type: Literal["advance_phase"] = "advance_phase"

    def validate(self, state: GameState) -> None:
        if state.phase == Phase.FINISHED:
            raise CommandError("Партия уже завершена")

    def apply(self, state: GameState, rng: Rng) -> GameState:
        order = [Phase.SETUP, Phase.DRAFT, Phase.PLAY, Phase.END_ROUND, Phase.FINISHED]
        state.phase = order[min(order.index(state.phase) + 1, len(order) - 1)]
        return state


AnyCommand = Annotated[
    Union[PassCommand, EndTurnCommand, DiscardCardCommand, PickDraftCardCommand, PlayCardCommand, PlayKompromatCommand,
          UseAbilityCommand, StartCombatCommand, RollCombatDieCommand,
          ResolveCombatRollCommand, PlaySituationalCommand, PassReactionCommand,
          ChooseInfluenceTokenCommand, ResolveKompromatCommand, ResolvePeekCommand,
          PickDiscardBuyCommand,
          ResolveSwapCommand,
          ResolvePlaceCommand,
          ResolveMoveCommand,
          ResolveMoveChoiceCommand,
          EventExplosionCommand,
          ResolveTokenSwapCommand,
          MayEventCommand,
          KazinoCommand,
          ResolveChoiceCommand,
          EventRollCommand,
          AckCombatResultCommand,
          AckMangyRollCommand,
          AckPenaltyCommand,
          AckEventCommand,
          AdvancePhaseCommand],
    Field(discriminator="type"),
]