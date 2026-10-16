"""Жетоны влияния (стартовые и наградные) + кубик.

Один кубик с 6 мастями (0..5). Каждая масть соответствует слоту на планшете:
боевой слот хранит боевой жетон, авторитетный — жетон авторитета.
- «Чёрная грань» = в слоте лежит НАГРАДНОЙ боевой жетон.
- «Белый жетон» = в слоте лежит НАГРАДНОЙ жетон авторитета.
- Значение проверки авторитета = числовое значение жетона авторитета в слоте.
"""
from .rng import Rng
from .state import GameState

# Информационные грани кубика (индексы 0..5) — сами по себе не несут действия;
# действие определяется жетоном в соответствующем слоте планшета (combat_line / authority_line).
DIE_FACES = ["кость", "лапа", "миска", "конура", "мячик", "ошейник"]

# Противоположные грани (для переворота кубика) — попарно, детерминированно:
#   миска(2) <-> конура(3)
#   мячик(4) <-> лапа(1)
#   кость(0)  <-> ошейник(5)
OPPOSITE_FACE = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 0}

# боевые жетоны: ключ -> {effect, reward}
COMBAT_TOKENS = {
    "attack":      {"effect": "attack",      "reward": False},
    "gop":         {"effect": "gop",         "reward": False},
    "self_gop":    {"effect": "self_gop",    "reward": False},
    "rob":         {"effect": "rob",         "reward": False},
    "move_dog":    {"effect": "move_dog",    "reward": False},
    "leave_trace": {"effect": "leave_trace", "reward": False},
    # наградные (чёрные)
    "attack_r":       {"effect": "attack",          "reward": True},
    "gop_r":          {"effect": "gop",             "reward": True},
    "extract":        {"effect": "extract",         "reward": True},
    "kompromat_opp":  {"effect": "kompromat_opp",   "reward": True},
}

# жетоны авторитета: ключ -> {value, effect, reward}
AUTHORITY_TOKENS = {
    "dummy":            {"value": 1, "effect": "dummy",              "reward": False},
    "place_money":      {"value": 2, "effect": "place_money",        "reward": False},
    "place_explosive":  {"value": 3, "effect": "place_explosive",    "reward": False},
    "take_money":       {"value": 4, "effect": "take_money",         "reward": False},
    "swap_card":        {"value": 5, "effect": "swap_card",          "reward": False},
    "take_resource":    {"value": 6, "effect": "take_resource",      "reward": False},
    # наградные (белые)
    "take_explosive_r": {"value": 3, "effect": "take_explosive",     "reward": True},
    "move_r":           {"value": 4, "effect": "move",               "reward": True},
    "swap_card_r":      {"value": 5, "effect": "swap_card_better",   "reward": True},
    "take_discard_r":   {"value": 6, "effect": "take_discard",       "reward": True},
}

STARTING_COMBAT = ["attack", "gop", "self_gop", "rob", "move_dog", "leave_trace"]
STARTING_AUTHORITY = ["dummy", "place_money", "place_explosive", "take_money", "swap_card", "take_resource"]
REWARD_COMBAT = ["attack_r", "gop_r", "extract", "kompromat_opp"]
REWARD_AUTHORITY = ["take_explosive_r", "move_r", "swap_card_r", "take_discard_r"]


def build_influence_bag() -> list[str]:
    """Мешок влияния: по 5 каждого наградного жетона (40 шт)."""
    bag = []
    for k in REWARD_COMBAT + REWARD_AUTHORITY:
        bag.extend([k] * 5)
    return bag


def is_combat_token(key: str) -> bool:
    return key in COMBAT_TOKENS


def authority_value(state: GameState, seat: int, face: int) -> int:
    return AUTHORITY_TOKENS[state.players[seat].authority_line[face]]["value"]


def authority_check(state: GameState, rng: Rng, seat: int) -> int:
    """Проверка авторитета: бросок кубика -> числовое значение жетона."""
    return authority_value(state, seat, rng.roll(6))


def is_black_face(state: GameState, seat: int, face: int) -> bool:
    return COMBAT_TOKENS[state.players[seat].combat_line[face]]["reward"]


def is_white_face(state: GameState, seat: int, face: int) -> bool:
    return AUTHORITY_TOKENS[state.players[seat].authority_line[face]]["reward"]


def combat_effect(state: GameState, seat: int, face: int) -> str:
    return COMBAT_TOKENS[state.players[seat].combat_line[face]]["effect"]


def is_explosion_death_face(state: GameState, seat: int, face: int) -> bool:
    """Гибель при взрыве: грань атаки ИЛИ чёрная грань."""
    return combat_effect(state, seat, face) == "attack" or is_black_face(state, seat, face)