from datetime import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from handlers.user.road.habits import get_habit_name, get_habit_notify_time
from handlers.user.road.states import FSM


@pytest.mark.parametrize("text", [None, "", "   "])
async def test_invalid_name_keeps_step(text):
    message: Any = SimpleNamespace(text=text, answer=AsyncMock())
    state: Any = SimpleNamespace(set_state=AsyncMock())
    data = {}

    await get_habit_name(message, state, data)

    state.set_state.assert_not_awaited()
    assert data == {}
    message.answer.assert_awaited_once()


@pytest.mark.parametrize("text", [None, "", "9:00", "24:00", "12:60", "abc"])
async def test_invalid_time_keeps_step_and_does_not_save(text):
    message: Any = SimpleNamespace(
        text=text, from_user=SimpleNamespace(id=1), answer=AsyncMock()
    )
    state: Any = SimpleNamespace(set_state=AsyncMock())
    data = {"habit_name": "Read"}

    with patch(
        "handlers.user.road.habits.Habits.create", new_callable=AsyncMock
    ) as create:
        await get_habit_notify_time(message, state, data)

    create.assert_not_awaited()
    state.set_state.assert_not_awaited()
    assert data == {"habit_name": "Read"}
    message.answer.assert_awaited_once()


async def test_valid_input_saves_habit():
    message: Any = SimpleNamespace(
        text="  Read  ", from_user=SimpleNamespace(id=1), answer=AsyncMock()
    )
    state: Any = SimpleNamespace(set_state=AsyncMock())
    data = {}
    await get_habit_name(message, state, data)
    state.set_state.assert_awaited_once_with(FSM.get_habit_notify_time)
    message.text = "09:30"
    with patch(
        "handlers.user.road.habits.Habits.create", new_callable=AsyncMock
    ) as create:
        await get_habit_notify_time(message, state, data)
    create.assert_awaited_once_with(user_id=1, name="Read", notify_time=time(9, 30))
    state.set_state.assert_awaited_with(FSM.finish)
