from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from .data import MiddlewareData, MiddlewareHandler
from .user_data_store import UserDataCapacityError, UserDataStore


class UserDataMiddleware(BaseMiddleware):
    def __init__(self, store: UserDataStore | None = None) -> None:
        self.store = store if store is not None else UserDataStore()

    @staticmethod
    def _session_active(state: str | None) -> bool:
        # Handlers use :finish as a terminal state, sometimes temporarily.
        # Only inspect it after the handler returns.
        return state is not None and state.rsplit(":", 1)[-1] != "finish"

    @staticmethod
    async def _notify(event: TelegramObject, text: str) -> None:
        if isinstance(event, (Message, CallbackQuery)):
            await event.answer(text)

    async def close(self) -> None:
        self.store.clear()

    async def __call__(  # type: ignore[override]  # pyright: ignore[reportIncompatibleMethodOverride]
        # Aiogram accepts dict[str, Any]; its docs recommend a TypedDict here.
        self,
        handler: MiddlewareHandler,
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            raise ValueError("Event does not contain a user.")

        state: FSMContext | None = data.get("state")
        if state is None:
            await self._notify(
                event,
                "Контекст сообщения недоступен. Отправь команду в нужном чате или теме.",
            )
            return None
        # Inline/inaccessible callbacks cannot identify their original topic safely.
        if isinstance(event, CallbackQuery) and not isinstance(event.message, Message):
            await self._notify(
                event, "Сообщение недоступно. Отправь команду в нужной теме."
            )
            return None
        key = state.key
        try:
            entry, created = self.store.acquire(key)
        except UserDataCapacityError:
            await self._notify(event, "Бот занят. Попробуйте ещё раз позже.")
            return None

        data["data"] = entry.values
        session_active = True
        try:
            # The selected FSM handler may need data lost to expiry or restart.
            # Stop it once and let the user restart instead of passing partial data.
            if created and self._session_active(await state.get_state()):
                await state.clear()
                await self._notify(event, "Сессия истекла. Запустите команду ещё раз.")
                return None
            return await handler(event, data)
        finally:
            try:
                session_active = self._session_active(await state.get_state())
            finally:
                self.store.release(key, entry, session_active=session_active)
