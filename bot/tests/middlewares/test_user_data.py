import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, TelegramObject, Update, User

from middlewares import setup
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


@pytest.mark.parametrize("max_entries", [0, -1])
def test_requires_positive_capacity(max_entries: int) -> None:
    with pytest.raises(ValueError, match="max_entries"):
        UserDataStore(max_entries=max_entries)


@pytest.mark.parametrize("idle_ttl", [0, -1, float("inf"), float("nan")])
def test_requires_finite_positive_ttl(idle_ttl: float) -> None:
    with pytest.raises(ValueError, match="idle_ttl"):
        UserDataStore(idle_ttl=idle_ttl)


async def test_expires_abandoned_session(store: UserDataStore, clock: Clock) -> None:
    entry, _ = store.acquire(1)
    entry.values["message"] = object()
    store.release(1, entry, session_active=True)

    clock.now = 10
    store.expire()

    assert len(store) == 0
    replacement, created = store.acquire(1)
    assert created
    assert replacement.values == {}
    store.release(1, replacement, session_active=False)


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
    store.release(1, entry, session_active=True)
    clock.now = 9
    same_entry, created = store.acquire(1)
    assert same_entry is entry
    assert not created
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
    second, created = store.acquire(1)
    assert second is first
    assert not created

    clock.now = 100
    store.expire()
    assert store.cleanup(1)
    store.release(1, first, session_active=False)
    assert len(store) == 1
    assert second.values["messages"] == ["prompt"]
    store.release(1, second, session_active=True)

    assert len(store) == 0
    assert not store.cleanup(1)
    assert first.values["messages"] == ["prompt"]


async def test_capacity_preserves_active_flows(store: UserDataStore) -> None:
    running, _ = store.acquire(1)
    waiting, _ = store.acquire(2)
    store.release(2, waiting, session_active=True)

    for user_id in range(3, 20):
        with pytest.raises(UserDataCapacityError):
            store.acquire(user_id)
        assert len(store) == 2
    same, _ = store.acquire(2)
    assert same is waiting
    store.release(2, same, session_active=True)
    store.release(1, running, session_active=False)


async def test_evicts_oldest_queue_before_live_session(
    store: UserDataStore, clock: Clock
) -> None:
    waiting, _ = store.acquire(1)
    store.release(1, waiting, session_active=True)
    queued, _ = store.acquire(2)
    queued.values["delete_queue"] = [object()]
    store.release(2, queued, session_active=False)

    clock.now = 1
    new, created = store.acquire(3)
    assert created
    assert len(store) == 2
    same, _ = store.acquire(1)
    assert same is waiting
    store.release(1, same, session_active=True)
    store.release(3, new, session_active=False)


async def test_finish_drops_context_but_keeps_queue_until_next_message(
    store: UserDataStore, state: FSMContext
) -> None:
    middleware = UserDataMiddleware(store)
    pending = AsyncMock()
    original: dict[str, Any] = {}

    async def finish(event: TelegramObject, data: dict[str, Any]) -> str:
        nonlocal original
        original = data["data"]
        original.update(messages=["history"], callback=object(), delete_queue=[pending])
        await state.set_state("FSM:finish")
        return "done"

    assert await middleware(finish, make_event(), {"state": state}) == "done"
    assert len(store) == 1

    async def next_message(event: TelegramObject, data: dict[str, Any]) -> None:
        assert data["data"] == {"delete_queue": []}
        assert data["data"] is not original

    async def with_delete_queue(event: TelegramObject, data: dict[str, Any]) -> None:
        await DeleteQueueMiddleware()(next_message, event, data)

    await middleware(with_delete_queue, make_event(), {"state": state})

    pending.delete.assert_awaited_once()
    assert original["messages"] == ["history"]
    assert len(store) == 0


@pytest.mark.parametrize("terminal_state", [None, "FSM:finish"])
async def test_session_completion_removes_entry(
    store: UserDataStore, state: FSMContext, terminal_state: str | None
) -> None:
    middleware = UserDataMiddleware(store)

    async def finish(event: TelegramObject, data: dict[str, Any]) -> None:
        data["data"]["text"] = "draft"
        await state.set_state(terminal_state)

    await middleware(finish, make_event(), {"state": state})

    assert len(store) == 0


async def test_busy_finish_does_not_expire_running_handler(
    store: UserDataStore, clock: Clock, state: FSMContext
) -> None:
    middleware = UserDataMiddleware(store)
    started, resume = asyncio.Event(), asyncio.Event()
    history = ["prompt"]

    async def generate(event: TelegramObject, data: dict[str, Any]) -> None:
        data["data"]["messages"] = history
        await state.set_state("FSM:finish")
        started.set()
        await resume.wait()
        assert data["data"]["messages"] is history
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

    async def continue_chat(event: TelegramObject, data: dict[str, Any]) -> None:
        assert data["data"]["messages"] is history
        await state.clear()

    await middleware(continue_chat, make_event(), {"state": state})
    assert len(store) == 0


@pytest.mark.parametrize("event_type", [Message, CallbackQuery])
@pytest.mark.parametrize("loss", ["expiry", "cleanup", "restart"])
async def test_missing_context_resets_stale_fsm_before_handler(
    store: UserDataStore,
    state: FSMContext,
    clock: Clock,
    event_type: type[TelegramObject],
    loss: str,
) -> None:
    middleware = UserDataMiddleware(store)

    async def start(event: TelegramObject, data: dict[str, Any]) -> None:
        data["data"]["messages"] = ["prompt"]
        await state.set_state("FSM:get_message")

    if loss != "restart":
        await middleware(start, make_event(), {"state": state})
        if loss == "expiry":
            clock.now = 10
            store.expire()
        else:
            store.cleanup(1)
    else:
        await state.set_state("FSM:get_message")
    await state.set_data({"draft": "stale"})
    event = make_event(event_type=event_type)
    handler = AsyncMock()

    result = await middleware(handler, event, {"state": state})

    assert result is None
    handler.assert_not_awaited()
    event.answer.assert_awaited_once_with("Сессия истекла. Запустите команду ещё раз.")
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

    async def start(message: Message, state: FSMContext, data: dict[str, Any]) -> None:
        data["messages"] = ["system"]
        await state.set_state("FSM:get_message")

    async def reply(message: Message, state: FSMContext, data: dict[str, Any]) -> None:
        assert message.text is not None
        data["messages"].append(message.text)
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
        request.assert_awaited_once()
        assert request.call_args.args[1].text == (
            "Сессия истекла. Запустите команду ещё раз."
        )
        await send("/chat", 4)
        await send("restarted", 5)
        assert replies == ["first", "restarted"]
    finally:
        await dispatcher.emit_shutdown()
        await bot.session.close()


async def test_capacity_response_does_not_run_handler(store: UserDataStore) -> None:
    first, _ = store.acquire(1)
    second, _ = store.acquire(2)
    event = make_event(3)
    handler = AsyncMock()

    await UserDataMiddleware(store)(handler, event, {})

    handler.assert_not_awaited()
    event.answer.assert_awaited_once_with("Бот занят. Попробуйте ещё раз позже.")
    store.release(1, first, session_active=False)
    store.release(2, second, session_active=False)


@pytest.mark.parametrize("error", [ValueError("failed"), asyncio.CancelledError()])
async def test_failure_releases_handler_pin(
    store: UserDataStore, state: FSMContext, clock: Clock, error: BaseException
) -> None:
    async def fail(event: TelegramObject, data: dict[str, Any]) -> None:
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
    state = MagicMock(spec=FSMContext)
    state.get_state = AsyncMock(side_effect=[None, OSError("storage unavailable")])

    with pytest.raises(OSError, match="storage unavailable"):
        await UserDataMiddleware(store)(AsyncMock(), make_event(), {"state": state})

    clock.now = 10
    store.expire()
    assert len(store) == 0


async def test_rejects_event_without_user(store: UserDataStore) -> None:
    event = make_event()
    event.from_user = None
    with pytest.raises(ValueError, match="does not contain a user"):
        await UserDataMiddleware(store)(AsyncMock(), event, {})
    assert len(store) == 0


async def test_setup_shares_store_and_shutdown_cancels_timers() -> None:
    dispatcher = Dispatcher()
    setup(dispatcher)
    message_middleware = next(
        item
        for item in dispatcher.message.middleware
        if isinstance(item, UserDataMiddleware)
    )
    callback_middleware = next(
        item
        for item in dispatcher.callback_query.middleware
        if isinstance(item, UserDataMiddleware)
    )
    assert message_middleware is callback_middleware
    entry, _ = message_middleware.store.acquire(1)
    message_middleware.store.release(1, entry, session_active=True)
    timer = entry.timer
    assert timer is not None

    await dispatcher.emit_shutdown()

    assert len(message_middleware.store) == 0
    assert timer.cancelled()


async def test_store_instances_are_independent(store: UserDataStore) -> None:
    other = UserDataStore()
    entry, _ = store.acquire(1)
    entry.values["messages"] = ["private"]
    other_entry, created = other.acquire(1)

    assert created
    assert other_entry.values == {}
    other.release(1, other_entry, session_active=False)
    store.release(1, entry, session_active=False)
