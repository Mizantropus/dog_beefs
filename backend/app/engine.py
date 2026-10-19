"""Игровой движок: цикл «загрузить -> валидация -> применение -> сохранить»."""
from .commands import Command, CommandError
from .rng import Rng
from .state import GameState, Phase
from .store import GameStore, VersionConflict, summarize


class GameNotFound(Exception):
    pass


class GameEngine:
    def __init__(self, store: GameStore | None = None):
        self.store = store or GameStore()

    async def dispatch(self, game_id: str, command: Command) -> GameState:
        for _ in range(8):
            state = await self.store.load(game_id)
            if state is None:
                raise GameNotFound(game_id)
            if state.phase == Phase.FINISHED:
                raise CommandError("Партия завершена")

            command.validate(state)

            rng = Rng.from_state(state.rng_state)
            work = state.model_copy(deep=True)
            new_state = command.apply(work, rng)

            new_state.version = state.version + 1
            new_state.rng_state = rng.state()

            try:
                await self.store.save(new_state)
            except VersionConflict:
                continue  # ретрай на свежей версии
            cmd = command.model_dump(mode="json")
            await self.store.log_move(game_id, new_state.version, command.seat, cmd, summarize(cmd, state))
            return new_state
        raise CommandError("Слишком много одновременных действий — попробуйте ещё раз")


engine = GameEngine()