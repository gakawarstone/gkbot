from dataclasses import replace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

import core.bot as bot_module
from core.bot import BotStarter
from core.types import BotConfig


def make_config() -> BotConfig:
    return BotConfig(
        token="12345678:ABCDEF-GHIJKLMNOPQRSTUV",
        startup_hooks=(),
        default_commands={},
        parse_mode="HTML",
        admins=[],
    )


def test_default_polling_limit() -> None:
    assert make_config().polling_tasks_concurrency_limit == 10


@pytest.mark.parametrize("limit", [1, 7, 100])
def test_positive_polling_limit(limit: int) -> None:
    assert (
        replace(
            make_config(), polling_tasks_concurrency_limit=limit
        ).polling_tasks_concurrency_limit
        == limit
    )


@pytest.mark.parametrize("limit", [0, -1, None, True, False, 1.5, "10"])
def test_invalid_polling_limit(limit: object) -> None:
    with pytest.raises(ValueError, match="polling_tasks_concurrency_limit"):
        replace(make_config(), polling_tasks_concurrency_limit=cast(int, limit))


@pytest.fixture
def polling_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bot_module.Notifier, "setup", AsyncMock())
    monkeypatch.setattr(bot_module.DefaultCommands, "set", AsyncMock())
    for module in (bot_module.middlewares, bot_module.handlers, bot_module.modules):
        monkeypatch.setattr(module, "setup", MagicMock())


@pytest.mark.usefixtures("polling_setup")
@pytest.mark.parametrize("limit", [None, 1, 7])
async def test_polling_forwards_configured_limit(
    monkeypatch: pytest.MonkeyPatch, limit: int | None
) -> None:
    config = (
        make_config()
        if limit is None
        else replace(make_config(), polling_tasks_concurrency_limit=limit)
    )
    starter = BotStarter(config)
    start_polling = AsyncMock()
    monkeypatch.setattr(starter.dp, "start_polling", start_polling)
    try:
        await starter._BotStarter__on_startup()  # type: ignore[attr-defined]
        start_polling.assert_awaited_once_with(
            starter.bot,
            handle_as_tasks=True,
            tasks_concurrency_limit=10 if limit is None else limit,
        )
    finally:
        await starter.bot.session.close()
