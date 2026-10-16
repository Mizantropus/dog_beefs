"""События: вытягивание карты и её разрешение."""
from . import influence, reactions, resources, tokens
from .buildings import controller
from .errors import CommandError
from .rng import Rng
from .state import GameState, Phase

# Добровольные события (каждый игрок может действовать или пропустить).
MAY_EVENTS = {"cherny_rynok_kompromata", "kredit", "subbotnik", "chernaya_pyatnitsa", "stroitelny_bum", "mobilizatsiya"}
# События с пошаговым броском кубика (проверка авторитета / масть).
EVENT_ROLL_EVENTS = {"lotereya", "rozygrysh_prizov", "igra_s_nulevoy_summoy", "russkaya_ruletka"}


def draw_event(state: GameState, rng: Rng) -> str | None:
    """Вытянуть верхнюю карту события (перетасовать сброс, если добор пуст)."""
    if not state.event_deck.draw:
        state.event_deck.draw = rng.shuffle(state.event_deck.discard)
        state.event_deck.discard = []
    if not state.event_deck.draw:
        return None
    return state.event_deck.draw.pop()


def draw_and_resolve_event(state: GameState, rng: Rng, actor_seat: int = 0) -> None:
    slug = draw_event(state, rng)
    if slug is None:
        return
    # «Коллекторы» до первого «Кредита» — замешать обратно
    if slug == "kollektory" and not state.credit_played:
        state.event_deck.draw.append(slug)
        state.event_deck.draw = rng.shuffle(state.event_deck.draw)
        state.pending_event = {"slug": slug, "acked": []}  # всплывашка объяснит замес
        return
    if slug == "kredit":
        state.credit_played = True
    resolve_event(state, rng, slug, actor_seat)
    state.event_deck.discard.append(slug)
    if slug in MAY_EVENTS:
        state.pending_may_event = {"slug": slug, "acted": [], "done": []}
    elif slug == "kazino":
        pass  # pending_kazino уже выставлен в resolve_event
    elif slug in EVENT_ROLL_EVENTS:
        pass  # pending_event_roll уже выставлен в resolve_event
    else:
        state.pending_event = {"slug": slug, "acked": []}


def resolve_event(state: GameState, rng: Rng, slug: str, actor_seat: int = 0) -> None:
    # --- деньги/ресурсы в случайные районы ---
    if slug in ("podderzhka_promyshlennosti", "podderzhka_zdravoohraneniya",
                "podderzhka_obrazovaniya", "podderzhka_molodyh_semey"):
        for d in rng.sample(state.board_districts, state.player_count):
            state.districts[d].money += 200
    elif slug in ("vsplesk_kriminala", "inoagenty"):
        for d in rng.sample(state.board_districts, state.player_count):
            state.districts[d].mangy += 1
    elif slug == "stoyanka_voennogo_eshelona":
        for d in rng.sample(state.board_districts, state.player_count):
            state.districts[d].explosives.append({"owner": None, "active": False})
    elif slug == "zalyotnye_pizhony":
        for d in rng.sample(state.board_districts, 2):
            state.districts[d].money += 200
            state.districts[d].mangy += 1
    # --- обязательные платежи ---
    elif slug == "imeniny_gubernatora":
        for p in state.players:
            p.money = max(0, p.money - 300)
    elif slug == "podderzhka_elektorata":
        for p in state.players:
            paid = min(200, p.money)
            if paid > 0:
                p.money -= paid
                state.districts[rng.choice(state.board_districts)].money += paid
    elif slug == "mobilizatsiya":
        pass  # через may_event_act (выбор пса каждым игроком)
    # --- мосты ---
    elif slug == "mostopad":
        _queue_mostopad(state, rng, actor_seat)
    elif slug == "remont_mosta":
        if state.broken_bridges:
            for p in state.players:
                p.money = max(0, p.money - 200)
            _queue_repair(state, rng, actor_seat)
    # --- проверки авторитета ---
    elif slug in ("lotereya", "rozygrysh_prizov", "igra_s_nulevoy_summoy"):
        _queue_event_roll(state, slug, actor_seat)
    elif slug == "kazino":
        _queue_kazino(state, actor_seat)
    # --- прочее ---
    elif slug == "bezumny_piroman":
        d = rng.choice(state.board_districts)
        state.districts[d].explosives.append({"owner": None, "active": False})
        state.districts[d].mangy += 1
        resources.explode_event(state, d)
    elif slug == "russkaya_ruletka":
        _queue_russkaya_ruletka(state, rng, actor_seat)
    elif slug == "epidemiya":
        _epidemiya(state, rng)
    elif slug == "kollektory":
        # перекладывается в draw_and_resolve_event (замешать, если кредит не игрался)
        for seat in state.debtors:
            _repay_debt(state, seat, 1200)
        state.debtors = []
    # --- «могут» (необязательные действия) — пока нет интерактивности ---
    elif slug in MAY_EVENTS:
        pass  # эффект через may_event_act
    else:
        raise CommandError(f"Неизвестное событие: {slug}")


def may_event_act(state: GameState, rng: Rng, seat: int, *,
                    target_seat: int | None = None, count: int = 1,
                    district_id: int | None = None, resource: str | None = None,
                    choice: str | None = None) -> None:
    """Действие игрока в добровольном событии."""
    pend = state.pending_may_event
    if pend is None or seat in pend.get("done", []):
        raise CommandError("Вы уже завершили участие")
    slug = pend["slug"]
    p = state.players[seat]
    if slug == "kredit":
        if seat in pend.get("acted", []):
            raise CommandError("Вы уже взяли кредит")
        p.money += 1000
        if seat not in state.debtors:
            state.debtors.append(seat)
        pend.setdefault("acted", []).append(seat)
    elif slug == "cherny_rynok_kompromata":
        if target_seat is None or target_seat == seat:
            raise CommandError("Укажите, на кого купить компромат")
        cost = 600 * max(1, count)
        if p.money < cost:
            raise CommandError("Недостаточно денег")
        p.money -= cost
        for _ in range(max(1, count)):
            p.kompromat.append(target_seat)
    elif slug == "mobilizatsiya":
        d = state.districts.get(district_id)
        if d is None or d.dogs.get(seat, 0) < 1:
            raise CommandError("Нужен ваш пёс в этом районе")
        d.dogs[seat] -= 1
        if d.dogs[seat] <= 0:
            del d.dogs[seat]
        pend.setdefault("acted", []).append(seat)
    elif slug == "stroitelny_bum":
        d = state.districts.get(district_id)
        if d is None:
            raise CommandError("Такого района нет")
        if d.building_owner is not None:
            raise CommandError("В районе уже есть здание")
        if controller(state, district_id) != seat:
            raise CommandError("Вы не контролируете район")
        cost = max(0, d.build_cost - 300)
        if p.money < cost:
            raise CommandError("Недостаточно денег")
        p.money -= cost
        d.building_owner = seat
        if state.phase == Phase.PLAY:
            influence.influence_for_build(state, seat, district_id)
    elif slug == "subbotnik":
        _subbotnik_pick(state, seat, district_id, resource)
    elif slug == "chernaya_pyatnitsa":
        _black_friday_buy(state, seat, choice, target_seat, district_id)
    else:
        raise CommandError("Неизвестное событие")


def may_event_done(state: GameState, seat: int) -> None:
    """Игрок завершил участие в добровольном событии."""
    pend = state.pending_may_event
    if pend is None:
        raise CommandError("Нет события")
    if pend["slug"] == "mobilizatsiya" and seat not in pend.get("acted", []):
        if _has_any_dog(state, seat):
            raise CommandError("Вы должны отдать одного пса")
    if seat not in pend.get("done", []):
        pend.setdefault("done", []).append(seat)
    if len(pend["done"]) >= state.player_count:
        state.pending_may_event = None


def _has_any_dog(state: GameState, seat: int) -> bool:
    for d in state.districts.values():
        if d.dogs.get(seat, 0) >= 1:
            return True
    return False


def _subbotnik_pick(state: GameState, seat: int, district_id: int | None, resource: str | None) -> None:
    d = state.districts.get(district_id)
    if d is None or d.dogs.get(seat, 0) < 1:
        raise CommandError("Нужен ваш пёс в районе")
    if controller(state, district_id) != seat:
        for s in range(state.player_count):
            if s != seat and (d.dogs.get(s, 0) > 0 or d.building_owner == s):
                raise CommandError("Район не подходит (не контроль и есть чужие фишки)")
    p = state.players[seat]
    if resource == "money":
        if d.money <= 0:
            raise CommandError("В районе нет денег")
        p.money += d.money
        d.money = 0
    elif resource == "explosive":
        for ex in list(d.explosives):
            if ex["owner"] == seat or not ex["active"]:
                d.explosives.remove(ex)
                p.explosives += 1
                return
        raise CommandError("Нет взрывчатки, которую можно просто забрать")
    elif resource == "kompromat":
        others = [t for t in d.kompromat if t != seat]
        if not others:
            raise CommandError("Здесь нет чужого компромата")
        t = others[0]
        d.kompromat.remove(t)
        p.kompromat.append(t)
    else:
        raise CommandError("Укажите ресурс")


def _black_friday_buy(state: GameState, seat: int, choice: str | None,
                      target_seat: int | None, district_id: int | None) -> None:
    """Чёрная пятница: купить единицу со скидкой 200$ (по зданиям игрока)."""
    p = state.players[seat]
    kinds = set()
    for d in state.districts.values():
        if d.building_owner == seat and d.ability:
            kinds.add(d.ability.get("kind"))
    cost = 0
    if choice == "mangy" and "spawn_mangy" in kinds:
        target = district_id if district_id is not None else _building_id(state, seat, "spawn_mangy")
        state.districts[target].mangy += 1
    elif choice == "dog" and "spawn_dog" in kinds:
        d = state.districts[_building_id(state, seat, "spawn_dog")]
        d.dogs[seat] = d.dogs.get(seat, 0) + 1
        cost = 100
    elif choice == "explosive" and "buy_explosive_or_discard" in kinds:
        p.explosives += 1
        cost = 400
    elif choice == "kompromat" and "buy_kompromat" in kinds:
        if target_seat is None:
            raise CommandError("Укажите, на кого купить компромат")
        p.kompromat.append(target_seat)
        cost = 600
    else:
        raise CommandError("Недоступный товар")
    if p.money < cost:
        raise CommandError("Недостаточно денег")
    p.money -= cost


def _building_id(state: GameState, seat: int, kind: str) -> int:
    for d in state.districts.values():
        if d.building_owner == seat and d.ability and d.ability.get("kind") == kind:
            return d.id
    raise CommandError("Нужное здание не найдено")


def _bridges_in(state: GameState, district_id: int) -> list:
    out = []
    for e in state.edges:
        if e["kind"] == "river" and (e["a"] == district_id or e["b"] == district_id):
            key = sorted([e["a"], e["b"]])
            if key not in out:
                out.append(key)
    return out


def _queue_mostopad(state: GameState, rng: Rng, actor_seat: int) -> None:
    districts = [d for d in rng.sample(state.board_districts, 2) if _bridges_in(state, d)]
    if not districts:
        return
    opts = _bridges_in(state, districts[0])
    state.pending_choice = {"seat": actor_seat, "kind": "break_bridge", "options": opts,
                            "context": {"remaining": districts[1:]}}


def _queue_repair(state: GameState, rng: Rng, actor_seat: int) -> None:
    if not state.broken_bridges:
        return
    # случайный район со сломанным мостом (мешочек жетонов), затем выбор внутри
    districts = set()
    for k in state.broken_bridges:
        districts.add(k[0]); districts.add(k[1])
    d = rng.choice(sorted(districts))
    opts = [k for k in state.broken_bridges if k[0] == d or k[1] == d]
    state.pending_choice = {"seat": actor_seat, "kind": "repair_bridge", "options": opts,
                            "context": {}}


def resolve_choice(state: GameState, value, rng: Rng) -> None:
    pc = state.pending_choice
    if pc is None:
        raise CommandError("Нет ожидающего выбора")
    kind = pc["kind"]
    if kind == "break_bridge":
        if value not in pc["options"]:
            raise CommandError("Неверный мост")
        if value not in state.broken_bridges:
            state.broken_bridges.append(value)
        remaining = pc["context"].get("remaining", [])
        if remaining:
            nxt = remaining[0]
            state.pending_choice = {"seat": pc["seat"], "kind": "break_bridge",
                                    "options": _bridges_in(state, nxt),
                                    "context": {"remaining": remaining[1:]}}
        else:
            state.pending_choice = None
    elif kind == "repair_bridge":
        if value not in pc["options"]:
            raise CommandError("Неверный мост")
        if value in state.broken_bridges:
            state.broken_bridges.remove(value)
        state.pending_choice = None
    elif kind == "combat_extract":
        keys = [o["key"] for o in pc["options"]]
        if value not in keys:
            raise CommandError("Неверное действие")
        from . import combat
        combat.resolve_extract_choice(state, rng, value, pc["context"])
        state.pending_choice = None
    else:
        raise CommandError("Неизвестный выбор")


# --- хелперы ---

def _authority_winner(state: GameState, rng: Rng) -> int | None:
    rolls = {p.seat: tokens.authority_check(state, rng, p.seat) for p in state.players}
    return max(rolls, key=rolls.get) if rolls else None


def _authority_winner_loser(state: GameState, rng: Rng) -> tuple[int | None, int | None]:
    rolls = {p.seat: tokens.authority_check(state, rng, p.seat) for p in state.players}
    if len(rolls) < 2:
        return None, None
    return max(rolls, key=rolls.get), min(rolls, key=rolls.get)


def _queue_event_roll(state: GameState, slug: str, actor_seat: int) -> None:
    n = state.player_count
    state.pending_event_roll = {
        "slug": slug,
        "order": [(actor_seat + i) % n for i in range(n)],
        "idx": 0, "results": {}, "rolled": False, "target": None,
    }


def _queue_russkaya_ruletka(state: GameState, rng: Rng, actor_seat: int) -> None:
    n = state.player_count
    state.pending_event_roll = {
        "slug": "russkaya_ruletka",
        "order": [(actor_seat + i) % n for i in range(n)],
        "idx": 0, "results": {}, "rolled": False,
        "target": rng.roll(6),  # масть, которую нужно повторить
    }


def event_roll(state: GameState, rng: Rng, seat: int, action: str) -> None:
    """Бросок в пошаговом событии (action = roll / ok)."""
    pend = state.pending_event_roll
    if pend is None:
        raise CommandError("Нет события с броском")
    current = pend["order"][pend["idx"]]
    if seat != current:
        raise CommandError("Сейчас не ваш ход")
    if action == "roll":
        if pend["rolled"]:
            raise CommandError("Вы уже бросили")
        face = rng.roll(6)
        pend.setdefault("faces", {})[str(current)] = face
        if pend["slug"] == "russkaya_ruletka":
            pend["results"][str(current)] = face  # выпавшая масть
            pend.setdefault("rewards", {})[str(current)] = False
        else:
            pend["results"][str(current)] = tokens.authority_value(state, current, face)
            pend.setdefault("rewards", {})[str(current)] = tokens.is_white_face(state, current, face)
        pend["rolled"] = True
        reactions.open_roll(state, current, "event")
    elif action == "ok":
        if not pend["rolled"]:
            raise CommandError("Сначала бросьте")
        _advance_event_roll(state, rng)
    else:
        raise CommandError("Неизвестное действие")


def _advance_event_roll(state: GameState, rng: Rng) -> None:
    pend = state.pending_event_roll
    slug = pend["slug"]
    if slug == "russkaya_ruletka":
        current = pend["order"][pend["idx"]]
        if pend["results"].get(str(current)) == pend["target"]:
            _remove_one_dog(state, current)
            state.pending_event_roll = None
            state.pending_event = {"slug": slug, "acked": []}
            return
    pend["idx"] += 1
    pend["rolled"] = False
    if pend["idx"] >= len(pend["order"]):
        _finish_event_roll(state, rng)


def _finish_event_roll(state: GameState, rng: Rng) -> None:
    pend = state.pending_event_roll
    slug = pend["slug"]
    results = pend["results"]
    if slug == "lotereya":
        for seat, val in results.items():
            seat = int(seat)
            if val <= 2:
                state.players[seat].money = max(0, state.players[seat].money - 200)
            elif val >= 5:
                state.players[seat].money += 200
    elif slug == "rozygrysh_prizov":
        winner = max(results, key=results.get) if results else None
        if winner is not None:
            state.players[int(winner)].explosives += 1
    elif slug == "igra_s_nulevoy_summoy":
        if len(results) >= 2:
            winner = int(max(results, key=results.get))
            loser = int(min(results, key=results.get))
            if winner != loser:
                state.players[winner].kompromat.append(loser)
    state.pending_event_roll = None
    state.pending_event = {"slug": slug, "acked": []}


def _break_one_bridge(state: GameState, district_id: int) -> None:
    for e in state.edges:
        if e["kind"] == "river" and (e["a"] == district_id or e["b"] == district_id):
            key = sorted([e["a"], e["b"]])
            if key not in state.broken_bridges:
                state.broken_bridges.append(key)
                return


def _remove_one_dog(state: GameState, seat: int) -> bool:
    for d in state.districts.values():
        if d.dogs.get(seat, 0) >= 1:
            d.dogs[seat] -= 1
            if d.dogs[seat] == 0:
                del d.dogs[seat]
            return True
    return False


def _russkaya_ruletka(state: GameState, rng: Rng, actor_seat: int) -> None:
    target = rng.roll(6)
    for i in range(state.player_count):
        seat = (actor_seat + i) % state.player_count
        if rng.roll(6) == target:
            _remove_one_dog(state, seat)
            return


def _epidemiya(state: GameState, rng: Rng) -> None:
    for d in rng.sample(state.board_districts, 3):
        dist = state.districts[d]
        dist.mangy = 0
        for seat in list(dist.dogs.keys()):
            survivors = 0
            for _ in range(dist.dogs[seat]):
                if tokens.authority_check(state, rng, seat) >= 3:
                    survivors += 1
            if survivors > 0:
                dist.dogs[seat] = survivors
            else:
                del dist.dogs[seat]


def _queue_kazino(state: GameState, actor_seat: int) -> None:
    n = state.player_count
    state.pending_kazino = {
        "pot": 0, "results": {}, "order": [(actor_seat + i) % n for i in range(n)],
        "idx": 0, "rolled": False, "rerolled": False,
    }


def kazino_roll(state: GameState, rng: Rng, seat: int, reroll: bool = False) -> None:
    pend = state.pending_kazino
    if pend is None:
        raise CommandError("Казино не идёт")
    current = pend["order"][pend["idx"]]
    if seat != current:
        raise CommandError("Сейчас не ваш ход")
    p = state.players[seat]
    if reroll:
        if not pend["rolled"]:
            raise CommandError("Сначала сделайте первый бросок")
        if pend["rerolled"]:
            raise CommandError("Вы уже перебрасывали")
        if p.money < 100:
            raise CommandError("Недостаточно денег для переброса")
        p.money -= 100
        pend["pot"] += 100
        pend["results"][seat] = tokens.authority_check(state, rng, seat)
        pend["rerolled"] = True
    else:
        if pend["rolled"]:
            raise CommandError("Вы уже бросили — перебросьте или завершите")
        paid = min(200, p.money)
        p.money -= paid
        pend["pot"] += paid
        pend["results"][str(seat)] = tokens.authority_check(state, rng, seat)
        pend["rolled"] = True
        reactions.open_roll(state, seat, "kazino")


def kazino_done(state: GameState, seat: int) -> None:
    pend = state.pending_kazino
    if pend is None:
        raise CommandError("Казино не идёт")
    current = pend["order"][pend["idx"]]
    if seat != current:
        raise CommandError("Сейчас не ваш ход")
    pend["idx"] += 1
    pend["rolled"] = False
    pend["rerolled"] = False
    if pend["idx"] >= len(pend["order"]):
        winner = max(pend["results"], key=pend["results"].get) if pend["results"] else None
        if winner is not None:
            state.players[int(winner)].money += pend["pot"]
        state.pending_kazino = None
        state.pending_event = {"slug": "kazino", "acked": []}

def _repay_debt(state: GameState, seat: int, amount: int) -> None:
    """Взыскать долг: деньги -> псы(400) -> компромат(600) -> взрывчатка(500) -> здания."""
    p = state.players[seat]
    paid = min(p.money, amount); p.money -= paid; amount -= paid
    while amount > 0 and _remove_one_dog(state, seat):
        amount -= 400
    while amount > 0 and p.kompromat:
        p.kompromat.pop(); amount -= 600
    while amount > 0 and p.explosives > 0:
        p.explosives -= 1; amount -= 500
    while amount > 0:
        b = _find_building(state, seat)
        if b is None:
            break
        amount -= b.build_cost
        b.building_owner = None


def _find_building(state: GameState, seat: int):
    for d in state.districts.values():
        if d.building_owner == seat:
            return d
    return None
