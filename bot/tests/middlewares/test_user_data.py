import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, TelegramObject, Update, User

from middlewares.data import MiddlewareData, UserData, require_user_data
from middlewares.delete_queue import DeleteQueueMiddleware
from middlewares.user_data import UserDataMiddleware
from middlewares.user_data_store import UserDataCapacityError, UserDataStore


@dataclass
class Clock:
    now: float = 0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def store(clock: Clock) -> Iterator[UserDataStore]:
    storage = UserDataStore(max_entries=2, idle_ttl=10, clock=clock)
    yield storage
    storage.clear()


@pytest.fixture
def state() -> FSMContext:
    return FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=1, user_id=1))


def make_event(
    user_id: int = 1, event_type: type[TelegramObject] = Message
) -> MagicMock:
    event = MagicMock(spec=event_type)
    event.from_user = MagicMock(id=user_id)
    event.answer = AsyncMock()
    return event


async def test_expiry_runs_without_another_update() -> None:
    store = UserDataStore(idle_ttl=0.01)
    entry, _ = store.acquire(1)
    store.release(1, entry, session_active=True)
    expired = asyncio.Event()
    asyncio.get_running_loop().call_later(0.02, expired.set)

    await asyncio.wait_for(expired.wait(), timeout=1)

    assert len(store) == 0


async def test_activity_refreshes_ttl(store: UserDataStore, clock: Clock) -> None:
    entry, _ = store.acquire(1)
    entry.values["messages"] = ["history"]
    store.release(1, entry, session_active=True)
    clock.now = 9
    same_entry, _ = store.acquire(1)
    assert same_entry.values.get("messages") == ["history"]
    store.release(1, same_entry, session_active=True)

    clock.now = 10
    store.expire()
    assert len(store) == 1
    clock.now = 19
    store.expire()
    assert len(store) == 0


async def test_cleanup_waits_for_all_handlers(
    store: UserDataStore, clock: Clock
) -> None:
    first, _ = store.acquire(1)
    first.values["messages"] = ["prompt"]
    second, _ = store.acquire(1)

    clock.now = 100
    store.expire()
    store.cleanup(1)
    store.release(1, first, session_active=False)
    assert len(store) == 1
    assert second.values.get("messages") == ["prompt"]
    store.release(1, second, session_active=True)

    assert len(store) == 0


async def test_capacity_preserves_active_flows(store: UserDataStore) -> None:
    running, _ = store.acquire(1)
    waiting, _ = store.acquire(2)
    waiting.values["messages"] = ["waiting for input"]
    store.release(2, waiting, session_active=True)

    for user_id in range(3, 20):
        with pytest.raises(UserDataCapacityError):
            store.acquire(user_id)
        assert len(store) == 2
    same, _ = store.acquire(2)
    assert same.values.get("messages") == ["waiting for input"]
    store.release(2, same, session_active=True)
    store.release(1, running, session_active=False)


async def test_capacity_discards_pending_queue_before_live_session(
    store: UserDataStore, clock: Clock
) -> None:
    waiting, _ = store.acquire(1)
    waiting.values["messages"] = ["conversation"]
    store.release(1, waiting, session_active=True)
    queued, _ = store.acquire(2)
    queued.values["delete_queue"] = [MagicMock(spec=Message)]
    store.release(2, queued, session_active=False)

    clock.now = 1
    new, _ = store.acquire(3)
    assert len(store) == 2
    same, _ = store.acquire(1)
    assert same.values.get("messages") == ["conversation"]
    store.release(1, same, session_active=True)
    store.release(3, new, session_active=False)


async def test_finish_drops_context_but_keeps_queue_until_next_message(
    store: UserDataStore, state: FSMContext
) -> None:
    middleware = UserDataMiddleware(store)
    pending = AsyncMock()

    async def finish(event: TelegramObject, data: MiddlewareData) -> None:
        user_data = require_user_data(data)
        user_data["messages"] = ["history"]
        user_data["callback"] = MagicMock()
        user_data["delete_queue"] = [pending]
        await state.set_state("FSM:finish")

    await middleware(finish, make_event(), {"state": state})
    assert len(store) == 1

    async def next_message(event: TelegramObject, data: MiddlewareData) -> None:
        assert require_user_data(data) == {"delete_queue": []}

    async def with_delete_queue(event: TelegramObject, data: MiddlewareData) -> None:
        await DeleteQueueMiddleware()(next_message, event, data)

    await middleware(with_delete_queue, make_event(), {"state": state})

    pending.delete.assert_awaited_once()
    assert len(store) == 0


async def test_busy_finish_does_not_expire_running_handler(
    store: UserDataStore, clock: Clock, state: FSMContext
) -> None:
    middleware = UserDataMiddleware(store)
    started, resume = asyncio.Event(), asyncio.Event()
    history = ["prompt"]

    async def generate(event: TelegramObject, data: MiddlewareData) -> None:
        require_user_data(data)["messages"] = history
        await state.set_state("FSM:finish")
        started.set()
        await resume.wait()
        assert require_user_data(data).get("messages") == history
        await state.set_state("FSM:get_message")

    task = asyncio.create_task(middleware(generate, make_event(), {"state": state}))
    try:
        await asyncio.wait_for(started.wait(), timeout=1)
        clock.now = 100
        store.expire()
        assert len(store) == 1
    finally:
        resume.set()
        await task

    async def continue_chat(event: TelegramObject, data: MiddlewareData) -> None:
        assert require_user_data(data).get("messages") == history
        await state.clear()

    await middleware(continue_chat, make_event(), {"state": state})
    assert len(store) == 0


async def test_callback_after_cleanup_resets_stale_fsm_before_handler(
    store: UserDataStore,
    state: FSMContext,
) -> None:
    middleware = UserDataMiddleware(store)

    async def start(event: TelegramObject, data: MiddlewareData) -> None:
        require_user_data(data)["messages"] = ["prompt"]
        await state.set_state("FSM:get_message")

    await middleware(start, make_event(), {"state": state})
    store.cleanup(1)
    await state.set_data({"draft": "stale"})
    event = make_event(event_type=CallbackQuery)
    handler = AsyncMock()

    result = await middleware(handler, event, {"state": state})

    assert result is None
    handler.assert_not_awaited()
    assert await state.get_state() is None
    assert await state.get_data() == {}
    assert len(store) == 0


async def test_dispatcher_skips_expired_handler_and_allows_restart(
    store: UserDataStore, clock: Clock, monkeypatch: pytest.MonkeyPatch
) -> None:
    dispatcher = Dispatcher()
    dispatcher.message.middleware(UserDataMiddleware(store))
    bot = Bot("12345678:ABCDEF-GHIJKLMNOPQRSTUV")
    request = AsyncMock(return_value=True)
    monkeypatch.setattr(bot.session, "make_request", request)
    replies: list[str] = []

    async def start(message: Message, state: FSMContext, data: UserData) -> None:
        data["messages"] = ["system"]
        await state.set_state("FSM:get_message")

    async def reply(message: Message, state: FSMContext, data: UserData) -> None:
        assert message.text is not None
        messages = data.get("messages")
        assert messages is not None
        messages.append(message.text)
        replies.append(message.text)

    dispatcher.message.register(start, Command("chat"))
    dispatcher.message.register(reply, StateFilter("FSM:get_message"))

    async def send(text: str, update_id: int) -> None:
        await dispatcher.feed_update(
            bot,
            Update(
                update_id=update_id,
                message=Message(
                    message_id=update_id,
                    date=datetime.now(UTC),
                    chat=Chat(id=1, type="private"),
                    from_user=User(id=1, is_bot=False, first_name="Test"),
                    text=text,
                ),
            ),
        )

    try:
        await send("/chat", 1)
        await send("first", 2)
        clock.now = 10
        store.expire()
        await send("expired", 3)
        assert replies == ["first"]
        assert request.call_args.args[1].text
        await send("/chat", 4)
        await send("restarted", 5)
        assert replies == ["first", "restarted"]
    finally:
        await dispatcher.emit_shutdown()
        await bot.session.close()


@pytest.mark.parametrize("error", [ValueError("failed"), asyncio.CancelledError()])
async def test_failure_releases_handler_pin(
    store: UserDataStore, state: FSMContext, clock: Clock, error: BaseException
) -> None:
    async def fail(event: TelegramObject, data: MiddlewareData) -> None:
        await state.set_state("FSM:get_message")
        raise error

    with pytest.raises(type(error)):
        await UserDataMiddleware(store)(fail, make_event(), {"state": state})

    assert len(store) == 1
    clock.now = 10
    store.expire()
    assert len(store) == 0


async def test_failed_fsm_lookup_still_releases_pin(
    store: UserDataStore, clock: Clock
) -> None:
    handler_finished = False

    async def get_state() -> str | None:
        if handler_finished:
            raise OSError("storage unavailable")
        return None

    async def finish(event: TelegramObject, data: MiddlewareData) -> None:
        nonlocal handler_finished
        handler_finished = True

    state = MagicMock(spec=FSMContext)
    state.get_state = AsyncMock(side_effect=get_state)

    with pytest.raises(OSError, match="storage unavailable"):
        await UserDataMiddleware(store)(finish, make_event(), {"state": state})

    clock.now = 10
    store.expire()
    assert len(store) == 0


async def test_store_instances_are_independent(store: UserDataStore) -> None:
    other = UserDataStore()
    entry, _ = store.acquire(1)
    entry.values["messages"] = ["private"]
    other_entry, _ = other.acquire(1)

    assert "messages" not in other_entry.values
    other.release(1, other_entry, session_active=False)
    store.release(1, entry, session_active=False)
