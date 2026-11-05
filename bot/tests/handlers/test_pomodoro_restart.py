from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from extensions.handlers.message.confirmation import ask_confirmation, choose_bool
from handlers.user.road.states import FSM
from middlewares.delete_queue import DeleteQueueMiddleware


@pytest.mark.parametrize(
    "answer, restarts", [("Да", True), ("y", True), ("Нет", False)]
)
async def test_restart_answer_consumes_callback_and_cleans_messages(
    answer: str, restarts: bool
) -> None:
    prompt = MagicMock(delete=AsyncMock())
    message = MagicMock(text=answer, delete=AsyncMock())
    callback = AsyncMock()
    state = MagicMock(set_state=AsyncMock())
    data: dict[str, Any] = {"delete_queue": []}
    origin = MagicMock(answer=AsyncMock(return_value=prompt))
    await ask_confirmation(
        origin, state, data, "Restart?", callback, FSM.choose_bool, FSM.finish
    )

    async def handle_update(event: object, context: dict) -> None:
        await choose_bool(message, state, context["data"])

    await DeleteQueueMiddleware()(handle_update, message, {"data": data})
    await choose_bool(message, state, data)

    prompt.delete.assert_awaited_once()
    message.delete.assert_awaited_once()
    assert state.set_state.await_args_list == [((FSM.choose_bool,),), ((FSM.finish,),)]
    assert "confirmation" not in data
    assert data["delete_queue"] == []
    assert callback.await_count == int(restarts)


async def test_confirmation_runs_no_callback() -> None:
    message = MagicMock(text="Нет", delete=AsyncMock())
    origin = MagicMock(answer=AsyncMock())
    state = MagicMock(set_state=AsyncMock())
    on_yes, on_no = AsyncMock(), AsyncMock()
    data: dict[str, Any] = {"delete_queue": []}

    await ask_confirmation(
        origin, state, data, "Continue?", on_yes, FSM.menu, FSM.start, on_no
    )
    await choose_bool(message, state, data)

    state.set_state.assert_awaited_with(FSM.start)
    on_yes.assert_not_awaited()
    on_no.assert_awaited_once()
    assert "confirmation" not in data
