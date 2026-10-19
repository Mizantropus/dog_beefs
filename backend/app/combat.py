"""Бой: псы против псов, псы против шелудивых.

Игроки по очереди кидают боевой кубик, пока одна из сторон не потеряет всех
псов (или всех шелудивых). После броска игрок может перевернуть кубик,
потратив компромат. Кубик шелудивых разыгрывается автоматически.

Грани кубика — информационные (миска, конура, мячик, лапа, кость, ошейник);
действие определяется жетоном в слоте планшета (combat_line игрока).
Противоположные грани см. tokens.OPPOSITE_FACE.
"""
from . import board, events, influence, reactions, tokens
from .errors import CommandError
from .round import next_turn
from .rng import Rng
from .state import CombatState, GameState, Phase

# Порядок стартовых жетонов боя (совпадает с PlayerState.combat_line по умолчанию).
COMBAT_TOKENS = ["attack", "gop", "self_gop", "rob", "move_dog", "leave_trace"]

# Грани кубика шелудивых (0..5).
MANGY_FACES = [
    "kill_dog",       # 0: шелудивые убивают одного вашего пса
    "dog_to_mangy",   # 1: один ваш пёс становится шелудивым
    "kompromat",      # 2: компромат на себя в район боя
    "recruit",        # 3: один шелудивый вербуется (становится вашим псом)
    "mangy_dies",     # 4: один шелудивый погибает
    "pay_100",        # 5: сбросьте 100$ в банк
]


def validate_start(state: GameState, attacker: int, district_id: int, defender: int | None) -> None:
    """Проверка возможности начать бой (чистая, без мутаций)."""
    if state.combat is not None:
        raise CommandError("Бой уже идёт")
    d = state.districts.get(district_id)
    if d is None:
        raise CommandError("Такого района нет")
    if d.dogs.get(attacker, 0) < 1:
        raise CommandError("Нужен хотя бы один ваш пёс в районе")
    if defender is not None:
        if defender == attacker:
            raise CommandError("Нельзя драться с самим собой")
        if d.dogs.get(defender, 0) < 1:
            raise CommandError("У соперника нет псов в районе")
    else:
        if d.mangy < 1:
            raise CommandError("В районе нет шелудивых")


def start_combat(state: GameState, attacker: int, district_id: int, defender: int | None) -> None:
    """Начать бой (вызывается после validate_start)."""
    d = state.districts[district_id]
    state.combat = CombatState(
        district_id=district_id,
        attacker=attacker,
        defender=defender,
        next_is_attacker=True,
        initial_mangy=d.mangy,
    )


def roll_combat(state: GameState, rng: Rng) -> None:
    """Бросок текущей стороны. Для игрока — кладёт pending (ждёт решения о перевороте);
    для шелудивых — применяет грань сразу и передаёт ход."""
    c = state.combat
    if c is None:
        raise CommandError("Бой не идёт")
    if c.pending is not None:
        raise CommandError("Сначала примените результат прошлого броска")

    if c.next_is_attacker or c.defender is not None:
        # бросок игрока (атакующего или защитника)
        face = rng.roll(6)
        c.pending = {"face": face, "opposite": tokens.OPPOSITE_FACE[face]}
        roller = c.attacker if c.next_is_attacker else c.defender
        reactions.open_roll(state, roller, "combat")
    else:
        # бросок шелудивых (показываем в панели боя, ждём «ОК»)
        face = rng.roll(6)
        _apply_mangy_effect(state, face)
        c.pending = {"face": face, "mangy": True}


def resolve_roll(state: GameState, rng: Rng, flip: bool, move_seat: int | None = None, move_to: int | None = None) -> None:
    """Применить ожидающий бросок игрока (flip=True — перевернуть кубик за компромат)."""
    c = state.combat
    if c is None or c.pending is None:
        raise CommandError("Нет ожидающего броска")
    roller = c.attacker if c.next_is_attacker else c.defender
    face = c.pending["opposite"] if flip else c.pending["face"]
    if flip:
        _spend_kompromat(state, roller, c)
    c.pending = None
    # игрок решил оставить грань — закрыть окно «Перебросить кубик», если оно ещё открыто
    if state.pending_reaction is not None and state.pending_reaction.get("trigger") == "roll":
        state.pending_reaction = None
    applied = _apply_combat_effect(state, roller, face, move_seat, move_to)
    if applied and state.pending_reaction is None:
        _advance(state)
        _check_end(state, rng)


def _spend_kompromat(state: GameState, roller: int, c: CombatState) -> None:
    if c.defender is not None:
        target = c.defender
        if target not in state.players[roller].kompromat:
            raise CommandError("Нет компромата на соперника")
        state.players[roller].kompromat.remove(target)
    else:
        if not state.players[roller].kompromat:
            raise CommandError("Нет компромата")
        state.players[roller].kompromat.pop()


def _advance(state: GameState) -> None:
    state.combat.next_is_attacker = not state.combat.next_is_attacker


def _apply_combat_effect(state: GameState, roller: int, face: int, move_seat: int | None = None, move_to: int | None = None) -> None:
    """Применить грань боевого кубика игрока roller (индекс в его combat_line)."""
    c = state.combat
    d = state.districts[c.district_id]
    # соперник бросающего: защитник бьёт атакующего, атакующий — защитника
    enemy = None if c.defender is None else (c.attacker if roller == c.defender else c.defender)
    effect = tokens.combat_effect(state, roller, face)

    if effect == "attack":
        if enemy is not None:
            if d.dogs.get(enemy, 0) >= 1:
                _dec_dog(state, enemy)
        else:
            if d.mangy >= 1:
                d.mangy -= 1
                c.mangy_killed_or_recruited += 1
    elif effect == "gop":
        if enemy is not None:
            if d.dogs.get(enemy, 0) >= 1:
                _transform_dog(state, enemy)
        else:
            if d.mangy >= 1:
                d.mangy -= 1
                d.dogs[roller] = d.dogs.get(roller, 0) + 1
                c.mangy_killed_or_recruited += 1
    elif effect == "self_gop":
        if d.dogs.get(roller, 0) >= 1:
            _transform_dog(state, roller)
    elif effect == "rob":
        if enemy is not None:
            steal = min(100, state.players[enemy].money)
            state.players[enemy].money -= steal
            state.players[roller].money += steal
        else:
            state.players[roller].money += 100  # из банка
    elif effect == "move_dog":
        if move_to is not None:
            _move_combat_piece(state, move_seat, move_to)
    elif effect == "leave_trace":
        if roller not in d.kompromat:
            d.kompromat.append(roller)
        # если компромат уже есть — осечка (упрощённо: ничего)
    elif effect == "extract":
        return _extract(state, roller, enemy, d)
    elif effect == "kompromat_opp":
        if enemy is not None:
            if enemy not in d.kompromat:
                d.kompromat.append(enemy)
            else:
                state.players[roller].kompromat.append(enemy)
        else:
            # бой с шелудивыми: выдаём компромат на себя в личный запас
            state.players[roller].kompromat.append(roller)
    return True


def _extract(state: GameState, roller: int, enemy: int | None, d) -> bool:
    """Жетон «Выбить»: выбор между 200$, компроматом из руки и компроматом из района."""
    options = []
    if roller in d.kompromat:
        options.append({"key": "district_kompromat", "text": "Поднять компромат на себя из района боя"})
    if enemy is not None and roller in state.players[enemy].kompromat:
        options.append({"key": "hand_kompromat", "text": "Забрать компромат на себя из руки противника"})
    if enemy is not None:
        options.append({"key": "steal_200", "text": "Выбить 200$ у противника"})
    else:
        options.append({"key": "steal_200", "text": "Взять 200$ из банка"})
    if len(options) > 1:
        state.pending_choice = {
            "seat": roller,
            "kind": "combat_extract",
            "options": options,
            "context": {"roller": roller, "enemy": enemy, "district_id": d.id},
        }
        return False
    _apply_extract_option(state, "steal_200", roller, enemy, d.id)
    return True


def _apply_extract_option(state: GameState, key: str, roller: int, enemy: int | None, district_id: int) -> None:
    d = state.districts[district_id]
    if key == "district_kompromat":
        if roller in d.kompromat:
            d.kompromat.remove(roller)
            state.players[roller].kompromat.append(roller)
    elif key == "hand_kompromat":
        if enemy is not None and roller in state.players[enemy].kompromat:
            state.players[enemy].kompromat.remove(roller)
            state.players[roller].kompromat.append(roller)
    else:  # steal_200
        if enemy is None:
            state.players[roller].money += 200  # из банка
        else:
            steal = min(200, state.players[enemy].money)
            state.players[enemy].money -= steal
            state.players[roller].money += steal


def resolve_extract_choice(state: GameState, rng: Rng, value: str, context: dict) -> None:
    """Применить выбранное действие жетона «Выбить» и продолжить бой."""
    _apply_extract_option(state, value, context["roller"], context["enemy"], context["district_id"])
    if state.pending_reaction is None:
        _advance(state)
        _check_end(state, rng)


def _apply_mangy_effect(state: GameState, face: int) -> None:
    """Применить грань кубика шелудивых (действует против атакующего)."""
    c = state.combat
    d = state.districts[c.district_id]
    atk = c.attacker
    name = MANGY_FACES[face]

    if name == "kill_dog":
        if d.dogs.get(atk, 0) >= 1:
            _dec_dog(state, atk)
    elif name == "dog_to_mangy":
        if d.dogs.get(atk, 0) >= 1:
            _transform_dog(state, atk)
    elif name == "kompromat":
        if atk not in d.kompromat:
            d.kompromat.append(atk)
    elif name == "recruit":
        if d.mangy >= 1:
            d.mangy -= 1
            d.dogs[atk] = d.dogs.get(atk, 0) + 1
            c.mangy_killed_or_recruited += 1
    elif name == "mangy_dies":
        if d.mangy >= 1:
            d.mangy -= 1
            c.mangy_killed_or_recruited += 1
    elif name == "pay_100":
        state.players[atk].money = max(0, state.players[atk].money - 100)


def _move_combat_piece(state: GameState, move_seat: int | None, move_to: int) -> None:
    """Переместить одного пса (seat) или шелудивого (None) из района боя в соседний."""
    combat_district = state.combat.district_id
    if not board.is_passable(state, combat_district, move_to):
        raise CommandError("Нужен соседний район")
    d = state.districts[combat_district]
    if move_seat is not None:
        c = state.combat
        if move_seat not in (c.attacker, c.defender):
            raise CommandError("Можно перемещать только псов участников боя")
        if d.dogs.get(move_seat, 0) < 1:
            raise CommandError("Нет такого пса в районе боя")
        d.dogs[move_seat] -= 1
        if d.dogs[move_seat] == 0:
            del d.dogs[move_seat]
        t = state.districts[move_to]
        t.dogs[move_seat] = t.dogs.get(move_seat, 0) + 1
    else:
        if d.mangy < 1:
            raise CommandError("Нет шелудивых в районе боя")
        d.mangy -= 1
        state.districts[move_to].mangy += 1


def _transform_dog(state: GameState, seat: int) -> None:
    """Превратить пса в шелудивого (не убийство — без окна «Броник»)."""
    d = state.districts[state.combat.district_id]
    d.dogs[seat] -= 1
    if d.dogs[seat] <= 0:
        del d.dogs[seat]
    d.mangy += 1


def _dec_dog(state: GameState, seat: int) -> None:
    """Попытаться убить пса (с окном реакции «Броник»)."""
    district_id = state.combat.district_id
    if reactions.open_dog_killed(state, seat, district_id):
        return  # окно; close убьёт или спасёт
    _kill_dog(state, seat, district_id)


def _kill_dog(state: GameState, seat: int, district_id: int) -> None:
    d = state.districts[district_id]
    d.dogs[seat] -= 1
    if d.dogs[seat] <= 0:
        del d.dogs[seat]


def _check_end(state: GameState, rng: Rng) -> None:
    """Проверка окончания боя; при завершении — записать результат и передать ход."""
    c = state.combat
    d = state.districts[c.district_id]
    atk = c.attacker

    if d.dogs.get(atk, 0) == 0:
        # атакующий потерял всех псов: выигрывает защитник (или никто, если бились с шелудивыми)
        _finish(state, rng, c.defender if c.defender is not None else None)
        return

    if c.defender is not None:
        if d.dogs.get(c.defender, 0) == 0:
            _finish(state, rng, atk)
    else:
        if d.mangy == 0:
            _finish(state, rng, atk)


def _finish(state: GameState, rng: Rng, winner: int | None) -> None:
    c = state.combat
    state.last_combat = {
        "winner": winner,
        "district_id": c.district_id,
        "vs_mangy": c.defender is None,
        "mangy_killed_or_recruited": c.mangy_killed_or_recruited,
        "initial_mangy": c.initial_mangy,
    }
    state.combat = None
    vp_before = state.players[winner].victory_points if winner is not None else 0
    # влияние за победу (если положено) + проверка победы
    influence.influence_for_combat(state)
    influence.check_win(state)
    if state.phase == Phase.FINISHED:
        return
    # событие за победу (если влияние начислено)
    if winner is not None and state.players[winner].victory_points > vp_before:
        if reactions.open_influence_gained(state, winner, next_action="combat_end",
                                           district_id=state.last_combat["district_id"]):
            return  # close -> событие + окно уборки мусора
        events.draw_and_resolve_event(state, rng, winner)
    # окно реакции «Уборка мусора»
    reactions.open_combat_ended(state, state.last_combat["district_id"])

def resume_combat_roll(state: GameState, rng: Rng) -> None:
    """После окна «Броник»: если есть текущий бросок — ждём «ОК», иначе продвигаем ход."""
    if state.combat is not None and state.combat.pending is not None:
        return  # ждём «ОК» по текущему броску (в т.ч. шелудивых)
    _advance(state)
    _check_end(state, rng)


def ack_combat_result(state: GameState, rng: Rng) -> None:
    """Атакующий подтвердил результат жетона боя (кнопка «ОК»)."""
    if state.pending_combat_result is None:
        raise CommandError("Нет результата боя для подтверждения")
    state.pending_combat_result = None
    _advance(state)
    _check_end(state, rng)


def ack_mangy_roll(state: GameState, rng: Rng) -> None:
    """Атакующий подтвердил бросок шелудивых (кнопка «ОК»)."""
    c = state.combat
    if c is None or c.pending is None or not c.pending.get("mangy"):
        raise CommandError("Нет броска шелудивых для подтверждения")
    c.pending = None
    _advance(state)
    _check_end(state, rng)
