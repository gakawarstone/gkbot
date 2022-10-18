from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from aiogram.fsm.context import FSMContext
from aiogram.handlers.base import BaseHandler as _BaseHandler
from aiogram.types import Message

_Callback = Callable[[Message, FSMContext, dict[str, Any]], Awaitable[Any]]


@dataclass
class _Context:
    callback: _Callback


class BaseHandler(_BaseHandler[Message]):
    @property
    def state(self):
        return self.data['state']

    @property
    def _data(self) -> dict[str, Any]:
        return self.data['data']

    @property
    def ctx(self) -> _Context:
        return _Context(
            callback=self._data['callback']
        )

    def _set_callback(self, callback: _Callback):
        self._data['callback'] = callback
