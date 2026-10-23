from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Bot, Dispatcher, Router
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import Message, Update

from configs.commands import USER_COMMANDS
from configs.default_commands import DEFAULT_COMMANDS
from handlers.user import setup as setup_user_router
from tests.mocks.message import make_fake_message


@pytest.mark.parametrize("command", ["add_tasks", "trash", "get_trash"])
async def test_retired_command_is_unhandled(command: str) -> None:
    dispatcher = Dispatcher()
    router = Router()
    setup_user_router(router)
    dispatcher.include_router(router)
    update = Update(update_id=1, message=make_fake_message(f"/{command}"))

    async with Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV") as bot:
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            result = await dispatcher.feed_update(bot, update)

    assert result is UNHANDLED
    answer.assert_not_awaited()
    assert command not in USER_COMMANDS.as_list()
    assert command not in DEFAULT_COMMANDS


async def test_command_list_omits_retired_commands() -> None:
    dispatcher = Dispatcher()
    router = Router()
    setup_user_router(router)
    dispatcher.include_router(router)
    update = Update(update_id=1, message=make_fake_message("/list"))

    async with Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV") as bot:
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            await dispatcher.feed_update(bot, update)

    answer.assert_awaited_once()
    assert answer.await_args is not None
    text = answer.await_args.args[0]
    assert "/list\n" in text
    assert "/add_tasks\n" not in text
    assert "/trash\n" not in text
    assert "/get_trash\n" not in text
