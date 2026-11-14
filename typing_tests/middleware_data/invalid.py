"""Each marked line must fail both mypy and pyright."""

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from extensions.handlers.message.base import BaseHandler
from middlewares.data import MiddlewareData


class Handler(BaseHandler):
    async def handle(self) -> None:
        pass


def check(message: Message) -> None:
    context: MiddlewareData = {}
    context["data"] = "not a dictionary"  # error
    context["state"] = "ready"  # error
    _state: FSMContext = context.get("state")  # error
    Handler(message, data="not a dictionary")  # error
    Handler(message, state="ready")  # error
