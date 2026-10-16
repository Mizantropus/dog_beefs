"""Детерминированный генератор случайных чисел.

Состояние ГСЧ хранится в `GameState.rng_state`, поэтому вся случайность:
- воспроизводима (один seed -> одна и та же партия);
- является частью версионированного снапшота (видна в логах, можно «переиграть»).

Правило использования:
- колоды и мешки тасуются ОДИН раз при подготовке, результат сохраняется в state,
  а вытягивание = pop из сохранённого списка (без повторного RNG);
- кубики и «случайный район» кидаются в момент действия через этот Rng,
  после чего новое состояние ГСЧ кладётся обратно в новый снапшот.
"""
import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class Rng:
    def __init__(self, seed=None):
        self._r = random.Random(seed)

    @classmethod
    def from_state(cls, state) -> "Rng":
        """Восстановить ГСЧ из сериализованного состояния (см. self.state())."""
        rng = cls.__new__(cls)
        rng._r = random.Random()
        if state:
            version, internal, gauss = state[0], tuple(state[1]), state[2]
            rng._r.setstate((version, internal, gauss))
        return rng

    def state(self) -> list:
        """Сериализуемое состояние: [version, [ints...], gauss]."""
        version, internal, gauss = self._r.getstate()
        return [version, list(internal), gauss]

    # --- примитивы ---

    def roll(self, sides: int = 6) -> int:
        """Индекс грани 0..sides-1 (кубики с символами/гранями)."""
        return self._r.randrange(sides)

    def roll_d6(self) -> int:
        """Число 1..6 (проверки вида «5–6 — успех»)."""
        return self._r.randint(1, 6)

    def shuffle(self, seq: Sequence[T]) -> list[T]:
        """Перемешанная копия последовательности."""
        s = list(seq)
        self._r.shuffle(s)
        return s

    def choice(self, seq: Sequence[T]) -> T:
        return self._r.choice(seq)

    def sample(self, seq: Sequence[T], k: int) -> list[T]:
        return self._r.sample(seq, k)

    def draw_bag(self, bag: Sequence[T], k: int) -> tuple[list[T], list[T]]:
        """Вытянуть k элементов из мешка без возврата -> (вытянутые, остаток)."""
        rest = list(bag)
        drawn = []
        for _ in range(k):
            drawn.append(rest.pop(self._r.randrange(len(rest))))
        return drawn, rest