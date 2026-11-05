from unittest.mock import AsyncMock, MagicMock

import pytest

from handlers.user.road.pomodoro.pomodoro import choose_bool
from handlers.user.road.states import FSM
from middlewares.delete_queue import DeleteQueueMiddleware


@pytest.mark.parametrize("answer, restarts", [("Да", True), ("y", True), ("Нет", False)])
async def test_restart_answer_consumes_callback_and_cleans_messages(
    answer: str, restarts: bool
) -> None:
    prompt = MagicMock(delete=AsyncMock())
    message = MagicMock(text=answer, delete=AsyncMock())
    callback = MagicMock(handle=AsyncMock())
    state = MagicMock(set_state=AsyncMock())
    data = {"callback": callback, "delete_queue": [prompt]}

    async def handle_update(event: object, context: dict) -> None:
        await choose_bool(message, state, context["data"])

    await DeleteQueueMiddleware()(handle_update, message, {"data": data})
    await choose_bool(message, state, data)

    prompt.delete.assert_awaited_once()
    message.delete.assert_awaited_once()
    state.set_state.assert_awaited_once_with(FSM.finish)
    assert "callback" not in data
    assert data["delete_queue"] == []
    assert callback.handle.await_count == int(restarts)
