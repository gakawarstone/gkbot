from dataclasses import replace
from typing import cast

import pytest

from core.types import BotConfig


def make_config() -> BotConfig:
    return BotConfig(
        token="12345678:ABCDEF-GHIJKLMNOPQRSTUV",
        startup_hooks=(),
        default_commands={},
        parse_mode="HTML",
        admins=[],
    )


@pytest.mark.parametrize("limit", [0, -1, None, True, 1.5, "10"])
def test_invalid_polling_limit(limit: object) -> None:
    with pytest.raises(ValueError, match="polling_tasks_concurrency_limit"):
        replace(make_config(), polling_tasks_concurrency_limit=cast(int, limit))
