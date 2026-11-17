from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

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

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            raise ValueError("Event does not contain a user.")

        try:
            entry, created = self.store.acquire(user.id)
        except UserDataCapacityError:
            await self._notify(event, "Бот занят. Попробуйте ещё раз позже.")
            return None

        data["data"] = entry.values
        state: FSMContext | None = data.get("state")
        session_active = state is not None
        try:
            # The selected FSM handler may need data lost to expiry or restart.
            # Stop it once and let the user restart instead of passing partial data.
            if (
                created
                and state is not None
                and self._session_active(await state.get_state())
            ):
                await state.clear()
                await self._notify(event, "Сессия истекла. Запустите команду ещё раз.")
                return None
            return await handler(event, data)
        finally:
            try:
                if state is not None:
                    session_active = self._session_active(await state.get_state())
            finally:
                self.store.release(user.id, entry, session_active=session_active)
