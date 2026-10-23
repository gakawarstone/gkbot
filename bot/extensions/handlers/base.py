from abc import ABC
from typing import Any, TypeVar

from aiogram.fsm.context import FSMContext
from aiogram.handlers import BaseHandler as _BaseHandler

from middlewares.data import MiddlewareData, UserData, require_user_data

Event = TypeVar("Event")


class BaseHandler(_BaseHandler[Event], ABC):
    def __init__(
        self,
        event: Event,
        *,
        data: UserData | None = None,
        state: FSMContext | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(event, data=data, state=state, **kwargs)
        self.context: MiddlewareData = {}
        if data is not None:
            self.context["data"] = data
        if state is not None:
            self.context["state"] = state

    @property
    def user_data(self) -> UserData:
        return require_user_data(self.context)

    @property
    def state(self) -> FSMContext:
        state = self.context.get("state")
        if state is None:
            raise RuntimeError("FSM middleware must provide state for this handler")
        return state

    def _try_get_from_user_data(self, prop: str) -> Any:
        # Legacy dataclass contexts use runtime field names. Their manager checks
        # values against the dataclass annotations before exposing them.
        return self.user_data.get(prop)
