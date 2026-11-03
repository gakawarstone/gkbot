import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from itertools import count
from typing import Any

import pytest
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import (
    CreateForumTopic,
    GetMe,
    SendMessage,
    SendMessageDraft,
    TelegramMethod,
)
from aiogram.types import (
    CallbackQuery,
    Chat,
    ForumTopic,
    Message,
    MessageGenerationStopped,
    Update,
    User,
)

from core.bot import BotStarter
from core.types import BotConfig
from handlers import error
from handlers.user import chatgpt, exit, topic
from handlers.user.chatgpt._states import FSM
from middlewares.data import UserData
from middlewares.user_data import UserDataMiddleware
from middlewares.user_data_store import UserDataStore
from services.llm.openrouter import OpenRouter, StreamChunk
from tests.handlers.test_chatgpt_drafts import RecordingSession


class TopicSession(RecordingSession):
    enabled = True
    next_topic = 100

    async def make_request(
        self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None
    ) -> Any:
        if isinstance(method, GetMe):
            self.requests.append(method)
            return User(
                id=bot.id,
                is_bot=True,
                first_name="Bot",
                has_topics_enabled=self.enabled,
            )
        if isinstance(method, CreateForumTopic):
            self.requests.append(method)
            if (failures := self.failures.get(type(method))) and (
                failure := failures.pop(0)
            ):
                raise failure
            self.next_topic += 1
            return ForumTopic(
                message_thread_id=self.next_topic, name=method.name, icon_color=7322096
            )
        return await super().make_request(bot, method, timeout)


class TopicApp:
    def __init__(self) -> None:
        self.starter = BotStarter(
            BotConfig(
                token="123456:TEST",
                startup_hooks=[],
                default_commands={},
                parse_mode="HTML",
                admins=[],
            )
        )
        self.bot = self.starter.bot
        self.session = TopicSession()
        self.bot.session = self.session
        self.dp = self.starter.dp
        self.store = UserDataStore()
        self.middleware = UserDataMiddleware(self.store)
        self.dp.message.middleware(self.middleware)
        self.dp.callback_query.middleware(self.middleware)
        self.ids = count(1)
        router = Router()
        topic.setup(router)
        exit.setup(router)
        chatgpt.setup(router)
        error.setup(router)

        async def callback(query: CallbackQuery, data: UserData) -> None:
            history = data.get("messages")
            if history is not None:
                history.append("callback")
            await query.answer()

        router.callback_query.register(callback)
        self.dp.include_router(router)

    async def send(
        self, text: str, thread: int | None, chat_type: str = "private"
    ) -> None:
        number = next(self.ids)
        await self.dp.feed_update(
            self.bot,
            Update(
                update_id=number,
                message=Message(
                    message_id=number,
                    date=datetime.now(UTC),
                    chat=Chat(id=7, type=chat_type),
                    from_user=User(id=7, is_bot=False, first_name="User"),
                    text=text,
                    message_thread_id=thread,
                    is_topic_message=thread is not None,
                ),
            ),
        )

    def state(self, thread: int | None) -> Any:
        state = self.dp.fsm.resolve_context(
            self.bot, chat_id=7, user_id=7, thread_id=thread
        )
        assert state is not None
        return state


@asynccontextmanager
async def app_context() -> AsyncIterator[TopicApp]:
    app = TopicApp()
    try:
        yield app
    finally:
        await app.middleware.close()
        await app.dp.storage.close()
        await app.bot.session.close()


async def test_concurrent_topics_callbacks_exit_and_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, resume = asyncio.Event(), asyncio.Event()
    prompts: list[str] = []

    async def stream(
        self: OpenRouter, prompt: str, images: list[str] | None = None
    ) -> AsyncGenerator[StreamChunk]:
        prompts.append(prompt)
        if prompt.endswith("slow A"):
            started.set()
            await resume.wait()
        yield StreamChunk("reply to " + prompt.split(" | ")[-1], "content")

    monkeypatch.setattr(OpenRouter, "stream", stream)
    async with app_context() as app:
        for thread in [11, 22, None]:
            await app.send("/chat", thread)
        task = asyncio.create_task(app.send("slow A", 11))
        try:
            await asyncio.wait_for(started.wait(), 2)
            await app.send("fast B", 22)
            await app.send("ordinary", None)
            assert await app.state(11).get_state() == FSM.finish.state
            assert await app.state(22).get_state() == FSM.get_message.state
            await app.dp.feed_update(
                app.bot,
                Update(
                    update_id=900,
                    callback_query=CallbackQuery(
                        id="callback",
                        chat_instance="chat",
                        from_user=User(id=7, is_bot=False, first_name="User"),
                        message=Message(
                            message_id=900,
                            date=datetime.now(UTC),
                            chat=Chat(id=7, type="private"),
                            message_thread_id=22,
                            is_topic_message=True,
                        ),
                    ),
                ),
            )
            await app.send("/exit", 22)
            assert await app.state(11).get_state() == FSM.finish.state
            assert await app.state(None).get_state() == FSM.get_message.state
        finally:
            resume.set()
            await task
        await app.send("again A", 11)
        await app.send("/chat", 22)
        await app.send("new B", 22)
        assert (
            "slow A" in prompts[3]
            and "fast B" not in prompts[3]
            and "ordinary" not in prompts[3]
            and "callback" not in prompts[3]
        )
        assert "fast B" not in prompts[4] and "slow A" not in prompts[4]
        replies = [
            r
            for r in app.session.requests
            if isinstance(r, SendMessage) and r.text.startswith("reply to")
        ]
        assert [(r.text, r.message_thread_id) for r in replies] == [
            ("reply to fast B", 22),
            ("reply to ordinary", None),
            ("reply to slow A", 11),
            ("reply to again A", 11),
            ("reply to new B", 22),
        ]


async def test_stop_and_upstream_error_stay_in_source_topic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, closed = asyncio.Event(), asyncio.Event()

    async def stream(
        self: OpenRouter, prompt: str, images: list[str] | None = None
    ) -> AsyncGenerator[StreamChunk]:
        if prompt.endswith("fail B"):
            raise ValueError("upstream failed")
        try:
            started.set()
            await asyncio.Event().wait()
            yield StreamChunk("unused", "content")
        finally:
            closed.set()

    monkeypatch.setattr(OpenRouter, "stream", stream)
    async with app_context() as app:
        await app.send("/chat", 11)
        await app.send("/chat", 22)
        task = asyncio.create_task(app.send("slow A", 11))
        try:
            await asyncio.wait_for(started.wait(), 2)
            draft = next(
                r for r in app.session.requests if isinstance(r, SendMessageDraft)
            )
            await app.dp.feed_update(
                app.bot,
                Update(
                    update_id=900,
                    stopped_message_generation=MessageGenerationStopped(
                        chat=Chat(id=7, type="private"),
                        message_thread_id=11,
                        draft_id=draft.draft_id,
                    ),
                ),
            )
            await asyncio.wait_for(task, 2)
            assert closed.is_set()
            assert await app.state(11).get_state() == FSM.get_message.state
            await app.send("fail B", 22)
            assert await app.state(22).get_state() == FSM.get_message.state
            statuses = [
                r
                for r in app.session.requests
                if isinstance(r, SendMessage)
                and ("остановлена" in r.text or "Не удалось обработать" in r.text)
            ]
            assert [r.message_thread_id for r in statuses] == [11, 22]
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)


async def test_topic_creation_preserves_existing_sessions_and_recovers_welcome_failure() -> (
    None
):
    async with app_context() as app:
        await app.send("/chat", 11)
        await app.send("/chat", 22)
        await app.send("/topic Учёба", 11)
        await app.send("/topic", 11)
        creates = [r for r in app.session.requests if isinstance(r, CreateForumTopic)]
        assert [r.name for r in creates] == ["Учёба", "AI-чат"]
        welcome = [
            r
            for r in app.session.requests
            if isinstance(r, SendMessage) and "отдельный AI-диалог" in r.text
        ]
        assert [r.message_thread_id for r in welcome] == [101, 102]
        await app.send("/chat", 101)
        assert (
            await app.state(11).get_state()
            == await app.state(22).get_state()
            == await app.state(101).get_state()
            == FSM.get_message.state
        )
        app.session.failures[SendMessage] = [
            TelegramBadRequest(
                method=SendMessage(chat_id=7, text="welcome"), message="topic deleted"
            )
        ]
        await app.send("/topic New", 11)
        assert isinstance(app.session.requests[-1], SendMessage)
        assert "Тема создана" in app.session.requests[-1].text
        assert app.session.requests[-1].message_thread_id == 11


@pytest.mark.parametrize("failure", ["group", "disabled", "name", "api", "network"])
async def test_unsupported_creation_never_changes_source_flow(failure: str) -> None:
    async with app_context() as app:
        await app.send("/chat", 11)
        if failure == "disabled":
            app.session.enabled = False
        if failure in {"api", "network"}:
            method = CreateForumTopic(chat_id=7, name="New")
            exception = (
                TelegramNetworkError if failure == "network" else TelegramBadRequest
            )
            app.session.failures[CreateForumTopic] = [
                exception(method=method, message="unavailable")
            ]
        before = len(app.session.requests)
        await app.send(
            "/topic " + ("x" * 129 if failure == "name" else "New"),
            11,
            "group" if failure == "group" else "private",
        )
        assert await app.state(11).get_state() == FSM.get_message.state
        assert not any(
            isinstance(r, SendMessageDraft) for r in app.session.requests[before:]
        )
        assert isinstance(app.session.requests[-1], SendMessage)
        assert app.session.requests[-1].message_thread_id == 11
