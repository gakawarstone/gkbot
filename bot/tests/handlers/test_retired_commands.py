from unittest.mock import AsyncMock, patch

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, Update

from handlers.user import setup as setup_user_router
from tests.mocks.message import make_fake_message


async def test_command_list_omits_retired_commands() -> None:
    dispatcher = Dispatcher()
    router = Router()
    setup_user_router(router)
    dispatcher.include_router(router)
    update = Update(update_id=1, message=make_fake_message("/list"))

    async with Bot(token="12345678:ABCDEF-GHIJKLMNOPQRSTUV") as bot:
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            await dispatcher.feed_update(bot, update)

    text = "\n".join(call.args[0] for call in answer.await_args_list)
    assert "/list\n" in text
    assert "/add_tasks\n" not in text
    assert "/trash\n" not in text
    assert "/get_trash\n" not in text
