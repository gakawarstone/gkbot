import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message

from modules.feed.handlers.messages import ShowFeedItemsHandler
from services.gkfeed import FeedItem, GkfeedCredentials


class LoggingHandler(ShowFeedItemsHandler):
    @property
    async def _gkfeed_credentials(self) -> GkfeedCredentials:
        return GkfeedCredentials(login="test", password="test")


@pytest.fixture
def item() -> FeedItem:
    return FeedItem(
        id=11,
        feed_id=22,
        link="https://example.invalid/private?token=" + "secret" * 1000,
        title="private title",
        text="data:image/jpeg;base64," + "private-payload" * 100_000,
    )


def assert_metadata_only(record: logging.LogRecord, item: FeedItem) -> None:
    assert record.args == (item.id, item.feed_id, len(item.text))
    assert len(record.getMessage()) < 120
    assert item.link not in record.getMessage()
    assert "private" not in record.getMessage()
    assert "base64" not in record.getMessage()


@pytest.mark.parametrize("has_item", [True, False])
async def test_handle_logs_only_item_metadata(
    item: FeedItem,
    has_item: bool,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    event = MagicMock(spec=Message)
    event.delete = AsyncMock()
    handler = LoggingHandler(event=event)
    picker = MagicMock()
    picker.get_next_item = AsyncMock(return_value=item if has_item else None)
    with (
        patch("modules.feed.handlers.messages.GkfeedItemsPicker", return_value=picker),
        patch.object(handler, "_process_item", new_callable=AsyncMock) as process,
        patch.object(handler, "answer", new_callable=AsyncMock) as answer,
        patch.object(FeedItem, "__repr__", side_effect=AssertionError("item repr")),
        caplog.at_level(logging.INFO, logger="modules.feed.handlers.messages"),
    ):
        await handler.handle()

    event.delete.assert_awaited_once()
    if has_item:
        process.assert_awaited_once_with(item)
        answer.assert_not_awaited()
        assert len(caplog.records) == 1
        assert_metadata_only(caplog.records[0], item)
        assert caplog.records[0].levelno == logging.INFO
    else:
        process.assert_not_awaited()
        answer.assert_awaited_once_with("На данный момент ничего нового")
        assert not caplog.records
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("fallback_fails", [False, True])
async def test_processor_logs_traceback_and_preserves_fallback(
    item: FeedItem,
    fallback_fails: bool,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    handler = LoggingHandler(event=MagicMock(spec=Message))
    processing_error = ValueError("processor failed")
    fallback_error = RuntimeError("fallback failed")
    with (
        patch.object(
            handler, "_process_base_item", new=AsyncMock(side_effect=processing_error)
        ),
        patch.object(
            handler,
            "_send_item",
            new=AsyncMock(side_effect=fallback_error if fallback_fails else None),
        ) as send,
        patch.object(FeedItem, "__repr__", side_effect=AssertionError("item repr")),
    ):
        if fallback_fails:
            with pytest.raises(RuntimeError) as raised:
                await handler._process_item(item)
            assert raised.value is fallback_error
        else:
            await handler._process_item(item)

    send.assert_awaited_once_with(item)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert_metadata_only(record, item)
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None
    assert record.exc_info[1] is processing_error
    assert record.exc_info[2] is not None
    assert "ValueError: processor failed" in caplog.text
    assert "private-payload" not in caplog.text
    assert capsys.readouterr().out == ""
