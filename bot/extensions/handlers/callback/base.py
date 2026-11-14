from abc import ABC
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.types import CallbackQuery


class BaseHandler(_BaseHandler[CallbackQuery], ABC):
    @property
    def user_data(self) -> dict:
        return self.data["data"]

    @property
    def state(self) -> FSMContext:
        return self.data["state"]

    def _try_get_from_user_data(self, prop: str) -> Any | None:
        if prop not in self.user_data:
            return None
        return self.user_data[prop]
