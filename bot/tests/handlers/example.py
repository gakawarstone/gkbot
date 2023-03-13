from typing import Any

from aiogram.handlers.base import BaseHandler

from tests.mocks.message import fake_message


class FakeHandler(BaseHandler):
    async def handle(self) -> Any:
        pass


async def test_handler():
    await FakeHandler(event=fake_message).handle()
