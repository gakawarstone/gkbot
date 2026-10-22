import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    DisabledButton,
    EphemeralMessageParameters,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputRichMessage,
    Message,
    MessageGenerationStopped,
)
from aiohttp import web

from handlers.button.delete_message import setup as setup_delete_callback
from handlers.user import admins
from handlers.user.chatgpt._states import FSM
from handlers.user.chatgpt.answer import AnswerHandler
from services.llm.openrouter import OpenRouter, StreamChunk


def message_payload(text: str = "hello", chat_type: str = "private") -> dict[str, Any]:
    return {
        "message_id": 42,
        "date": 1_790_000_000,
        "chat": {"id": 1234, "type": chat_type},
        "from": {"id": 1234, "is_bot": False, "first_name": "User"},
        "text": text,
    }


@dataclass
class BotAPIStub:
    bot: Bot
    responses: dict[str, Any] = field(default_factory=dict)
    requests: list[tuple[str, dict[str, Any]]] = field(default_factory=list)


@pytest_asyncio.fixture(loop_scope="function")
async def api(unused_tcp_port: int) -> AsyncIterator[BotAPIStub]:
    session = AiohttpSession(
        api=TelegramAPIServer.from_base(f"http://127.0.0.1:{unused_tcp_port}"),
        timeout=2,
    )
    bot = Bot(
        "12345678:TEST_TOKEN",
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    stub = BotAPIStub(bot)

    async def respond(request: web.Request) -> web.Response:
        method = request.match_info["method"]
        data = {
            name: {"filename": value.filename, "content": value.file.read()}
            if isinstance(value, web.FileField)
            else value
            for name, value in (await request.post()).items()
        }
        stub.requests.append((method, data))
        assert method in stub.responses, f"Unexpected Bot API call: {method}"
        result = stub.responses[method]
        if method == "getUpdates":
            # Deliver the batch once, then allow the poller to wait for more updates.
            stub.responses[method] = []
            if not result:
                await asyncio.sleep(0.01)
        return web.json_response({"ok": True, "result": result})

    app = web.Application()
    app.router.add_post("/bot{token}/{method}", respond)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        await web.TCPSite(runner, "127.0.0.1", unused_tcp_port).start()
        yield stub
    finally:
        await bot.session.close()
        await runner.cleanup()


async def test_polling_dispatches_updates_and_sends_html(api: BotAPIStub) -> None:
    dispatcher = Dispatcher()
    handled = asyncio.Event()

    async def echo(message: Message) -> None:
        await message.answer("<b>hello</b>")
        handled.set()

    dispatcher.message.register(echo)
    api.responses.update(
        getMe={
            "id": api.bot.id,
            "is_bot": True,
            "first_name": "Bot",
            "username": "test_bot",
        },
        getUpdates=[{"update_id": 1, "message": message_payload()}],
        sendMessage=message_payload("hello"),
    )
    polling = asyncio.create_task(
        dispatcher.start_polling(
            api.bot,
            polling_timeout=1,
            tasks_concurrency_limit=1,
            handle_signals=False,
            close_bot_session=False,
        )
    )
    try:
        await asyncio.wait_for(handled.wait(), timeout=3)
        await asyncio.wait_for(dispatcher.stop_polling(), timeout=3)
        await asyncio.wait_for(polling, timeout=3)
    finally:
        if not polling.done():
            polling.cancel()
        await asyncio.gather(polling, return_exceptions=True)

    polling_request = next(
        data for method, data in api.requests if method == "getUpdates"
    )
    assert json.loads(polling_request["allowed_updates"]) == ["message"]
    assert polling_request["timeout"] == "1"
    sent = next(data for method, data in api.requests if method == "sendMessage")
    assert sent["text"] == "<b>hello</b>"
    assert sent["parse_mode"] == "HTML"


async def test_existing_delete_callback(api: BotAPIStub) -> None:
    dispatcher = Dispatcher()
    router = Router()
    setup_delete_callback(router)
    dispatcher.include_router(router)
    api.responses["deleteMessage"] = True

    await dispatcher.feed_raw_update(
        api.bot,
        {
            "update_id": 2,
            "callback_query": {
                "id": "callback-1",
                "from": message_payload()["from"],
                "chat_instance": "chat-1",
                "data": "del_msg",
                "message": message_payload(),
            },
        },
    )

    assert api.requests == [("deleteMessage", {"chat_id": "1234", "message_id": "42"})]


async def test_admins_with_bot_api_10_3_response(api: BotAPIStub) -> None:
    dispatcher = Dispatcher()
    router = Router()
    admins.setup(router)
    dispatcher.include_router(router)
    api.responses["getChatAdministrators"] = [
        {
            "status": "administrator",
            "user": {
                "id": 7,
                "is_bot": False,
                "first_name": "Admin",
                "username": "admin",
            },
            "can_be_edited": False,
            "is_anonymous": False,
            "can_manage_chat": True,
            "can_delete_messages": True,
            "can_manage_video_chats": True,
            "can_restrict_members": True,
            "can_promote_members": True,
            "can_change_info": True,
            "can_invite_users": True,
            "can_post_stories": False,
            "can_edit_stories": False,
            "can_delete_stories": False,
            "can_send_welcome_messages": False,
        }
    ]
    api.responses["sendMessage"] = message_payload("@admin", "supergroup")
    message = message_payload("/admins", "supergroup")
    message["entities"] = [{"type": "bot_command", "offset": 0, "length": 7}]

    await dispatcher.feed_raw_update(api.bot, {"update_id": 3, "message": message})

    assert [method for method, _ in api.requests] == [
        "getChatAdministrators",
        "sendMessage",
    ]
    assert api.requests[-1][1]["text"] == "@admin"


async def test_media_upload_and_html_caption(api: BotAPIStub) -> None:
    api.responses["sendPhoto"] = {
        **message_payload(),
        "photo": [
            {"file_id": "photo-id", "file_unique_id": "unique", "width": 1, "height": 1}
        ],
    }

    message = await api.bot.send_photo(
        1234,
        BufferedInputFile(b"photo bytes", filename="photo.jpg"),
        caption="<b>photo</b>",
    )

    assert message.photo is not None
    assert message.photo[0].file_id == "photo-id"
    method, data = api.requests[0]
    assert method == "sendPhoto"
    assert data["caption"] == "<b>photo</b>"
    assert data["parse_mode"] == "HTML"
    attachment = data[data["photo"].removeprefix("attach://")]
    assert attachment == {"filename": "photo.jpg", "content": b"photo bytes"}


async def test_ai_chat_stream_edits_message_and_returns_to_input(
    api: BotAPIStub, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def stream(
        self: OpenRouter, prompt: str, images: list[str] | None = None
    ) -> AsyncIterator[StreamChunk]:
        assert prompt == "Explain"
        assert images is None
        yield StreamChunk("**answer**", "content")

    monkeypatch.setattr(OpenRouter, "stream", stream)
    api.responses.update(
        sendMessage=message_payload("wait"), editMessageText=message_payload("answer")
    )
    message = Message.model_validate(
        message_payload("Explain"), context={"bot": api.bot}
    )
    storage = MemoryStorage()
    state = FSMContext(
        storage, StorageKey(bot_id=api.bot.id, chat_id=1234, user_id=1234)
    )
    user_data: dict[str, Any] = {"messages": []}
    handler = AnswerHandler(message, state=state, data=user_data)
    try:
        await handler.handle()
        assert await state.get_state() == FSM.get_message.state
    finally:
        await storage.close()

    assert user_data["messages"] == ["Explain", "**answer**"]
    assert [method for method, _ in api.requests] == ["sendMessage", "editMessageText"]
    assert api.requests[-1][1]["text"] == "<b>answer</b>"
    assert api.requests[-1][1]["parse_mode"] == "HTML"


async def test_bot_api_10_3_request_contract(api: BotAPIStub) -> None:
    api.responses.update(
        sendMessage=message_payload(),
        sendMessageDraft=True,
        sendRichMessage=message_payload(),
    )
    await api.bot.send_message(
        1234,
        "done",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="done", disabled=DisabledButton())]
            ]
        ),
        ephemeral_message_parameters=EphemeralMessageParameters(
            receiver_user_id=1234,
            callback_query_id="callback-1",
            replace_callback_query_message=True,
        ),
    )
    await api.bot.send_message_draft(
        1234, 1, text="<b>draft</b>", can_stop=True, keep_on_stop=True
    )
    await api.bot.send_rich_message(1234, InputRichMessage(html="<b>rich</b>"))

    sent = api.requests[0][1]
    button = json.loads(sent["reply_markup"])["inline_keyboard"][0][0]
    assert button == {"text": "done", "disabled": {}}
    assert json.loads(sent["ephemeral_message_parameters"]) == {
        "receiver_user_id": 1234,
        "callback_query_id": "callback-1",
        "replace_callback_query_message": True,
    }
    draft = api.requests[1][1]
    assert draft["can_stop"] == "true"
    assert draft["keep_on_stop"] == "true"
    assert draft["parse_mode"] == "HTML"
    assert json.loads(api.requests[2][1]["rich_message"]) == {"html": "<b>rich</b>"}


async def test_generation_stopped_update_is_routed(api: BotAPIStub) -> None:
    dispatcher = Dispatcher()
    received: list[MessageGenerationStopped] = []

    async def on_stopped(event: MessageGenerationStopped) -> None:
        received.append(event)

    dispatcher.stopped_message_generation.register(on_stopped)
    await dispatcher.feed_raw_update(
        api.bot,
        {
            "update_id": 4,
            "stopped_message_generation": {
                "chat": {"id": 1234, "type": "private"},
                "draft_id": 1,
            },
        },
    )

    assert dispatcher.resolve_used_update_types() == ["stopped_message_generation"]
    assert len(received) == 1
    assert received[0].draft_id == 1
    assert received[0].chat.id == 1234
