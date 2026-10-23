"""This fixture must pass both mypy and pyright."""

from datetime import timedelta
from typing import assert_type

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from extensions.handlers.message.base import BaseHandler
from middlewares.data import MiddlewareData, UserData, require_user_data


class Handler(BaseHandler):
    async def handle(self) -> None:
        assert_type(self.user_data, UserData)
        assert_type(self.state, FSMContext)


def check(message: Message, bot: Bot, state: FSMContext) -> None:
    user_data: UserData = {"delete_queue": []}
    context: MiddlewareData = {"data": user_data, "bot": bot, "state": state}
    assert_type(require_user_data(context), UserData)
    assert_type(user_data["delete_queue"], list[Message])
    assert_type(user_data.get("tz"), timedelta | None)
    assert_type(context.get("state"), FSMContext | None)
    user_data["tz"] = timedelta(hours=3)
    user_data["delete_queue"].append(message)
    Handler(message, data=user_data, state=state, bot=bot)
    if "data" in context:
        assert_type(context["data"], UserData)
    if "state" in context:
        assert_type(context["state"], FSMContext)
