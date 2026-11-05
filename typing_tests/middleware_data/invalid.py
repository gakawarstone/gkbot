"""Each marked line must fail both mypy and pyright."""

from datetime import timedelta

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from extensions.handlers.message.base import BaseHandler
from middlewares.data import MiddlewareData, UserData


class Handler(BaseHandler):
    async def handle(self) -> None:
        pass


def check(message: Message) -> None:
    _missing_queue: UserData = {}  # error
    user_data: UserData = {"delete_queue": []}
    user_data["tz"] = "UTC"  # error
    user_data["delete_queue"].append(42)  # error
    user_data["delete_queu"] = []  # error
    _timezone: timedelta = user_data.get("tz")  # error
    context: MiddlewareData = {}
    context["data"] = {"delete_queue": [42]}  # error
    context["state"] = "ready"  # error
    _state: FSMContext = context.get("state")  # error
    Handler(message, data={})  # error
    Handler(message, state="ready")  # error
