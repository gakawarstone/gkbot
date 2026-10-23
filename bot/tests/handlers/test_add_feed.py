from html import escape, unescape
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.feed.handlers.add._states import FSM
from modules.feed.handlers.add.add import AddFeedHandler
from services.gkfeed import GkfeedApi, GkfeedAuthService, GkfeedCredentials


@pytest.mark.parametrize(
    "feed_url",
    [
        "https://example.com/feed.xml?tag=<python>&sort=new#latest",
        "https://example.com/" + "я" * 236,
        "https://example.com/" + "a" * 237,
    ],
)
async def test_add_feed_confirmation_copies_saved_url(
    monkeypatch: pytest.MonkeyPatch, feed_url: str
) -> None:
    credentials = GkfeedCredentials(login="test", password="test")
    get_credentials = AsyncMock(return_value=credentials)
    add_feed = AsyncMock()
    monkeypatch.setattr(GkfeedAuthService, "get_credentials", get_credentials)
    monkeypatch.setattr(GkfeedApi, "add_feed_lazy", add_feed)
    event = MagicMock()
    event.text = feed_url
    event.from_user.id = 42
    event.delete = AsyncMock()
    event.answer = AsyncMock()
    state = MagicMock(set_state=AsyncMock())

    await AddFeedHandler(event=event, state=state).handle()

    state.set_state.assert_awaited_once_with(FSM.finish)
    event.delete.assert_awaited_once_with()
    get_credentials.assert_awaited_once_with(42)
    add_feed.assert_awaited_once_with(feed_url)
    event.answer.assert_awaited_once()
    args, kwargs = event.answer.await_args
    assert args == (f"Feed added: {escape(feed_url)}",)
    assert unescape(args[0]) == f"Feed added: {feed_url}"
    markup = kwargs["reply_markup"]
    if len(feed_url) <= 256:
        assert markup.inline_keyboard[0][0].copy_text.text == feed_url
    else:
        assert markup is None


async def test_add_feed_failure_does_not_offer_copy_button(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        GkfeedAuthService,
        "get_credentials",
        AsyncMock(return_value=GkfeedCredentials(login="test", password="test")),
    )
    monkeypatch.setattr(
        GkfeedApi, "add_feed_lazy", AsyncMock(side_effect=ValueError("Feed rejected"))
    )
    event = MagicMock()
    event.text = "https://example.com/feed.xml"
    event.delete = AsyncMock()
    event.answer = AsyncMock()

    with pytest.raises(ValueError, match="Feed rejected"):
        await AddFeedHandler(
            event=event, state=MagicMock(set_state=AsyncMock())
        ).handle()

    event.answer.assert_not_awaited()
