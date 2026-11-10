from unittest.mock import AsyncMock, MagicMock

import pytest

from handlers.user.tasks import get_deadline


@pytest.mark.parametrize(
    "failure", [OSError("Notion unavailable"), ValueError("bad property")]
)
async def test_valid_deadline_preserves_storage_failures(
    failure: Exception,
) -> None:
    row = MagicMock(set_date=AsyncMock(side_effect=failure), set_select=AsyncMock())
    state = MagicMock(
        set_state=AsyncMock(), get_data=AsyncMock(return_value={"row": row})
    )
    message = MagicMock(text="23.10.2026", answer=AsyncMock())

    with pytest.raises(type(failure)) as raised:
        await get_deadline(message, state)
    assert raised.value is failure
    message.answer.assert_not_awaited()
