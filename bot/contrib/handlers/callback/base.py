from abc import ABC
from typing import Any, Optional

from aiogram.handlers import BaseHandler as _BaseHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


class BaseHandler(_BaseHandler[CallbackQuery], ABC):
    @property
    def user_data(self) -> dict:
        return self.data['data']

    @property
    def state(self) -> FSMContext:
        return self.data['state']

    def _try_get_from_user_data(self, prop: str) -> Optional[Any]:
        if prop not in self.user_data.keys():
            return None
        return self.user_data[prop]
