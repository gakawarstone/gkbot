from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from handlers.user.tasks import TaskStates, get_deadline


@pytest.mark.parametrize("text", [None, "invalid", "31.02.2026"])
async def test_invalid_deadline_does_not_write_to_notion(text: str | None) -> None:
    message = MagicMock(text=text, answer=AsyncMock())
    state = MagicMock(set_state=AsyncMock(), get_data=AsyncMock())

    await get_deadline(message, state)

    state.set_state.assert_awaited_with(TaskStates.deadline)
    state.get_data.assert_not_awaited()
    message.answer.assert_awaited_once_with("Дата некорректна [01.01.1970]")


@pytest.mark.parametrize(
    "failure", [None, OSError("Notion unavailable"), ValueError("bad property")]
)
async def test_valid_deadline_preserves_storage_failures(
    failure: Exception | None,
) -> None:
    row = MagicMock(set_date=AsyncMock(side_effect=failure), set_select=AsyncMock())
    state = MagicMock(
        set_state=AsyncMock(), get_data=AsyncMock(return_value={"row": row})
    )
    message = MagicMock(text="23.10.2026", answer=AsyncMock())

    if failure is not None:
        with pytest.raises(type(failure)) as raised:
            await get_deadline(message, state)
        assert raised.value is failure
        message.answer.assert_not_awaited()
        row.set_select.assert_not_awaited()
    else:
        await get_deadline(message, state)
        row.set_select.assert_awaited_once_with("Status", "Не начато")
        message.answer.assert_awaited_once_with("Спасибо")
    row.set_date.assert_awaited_once_with("Deadline", datetime(2026, 10, 23))
