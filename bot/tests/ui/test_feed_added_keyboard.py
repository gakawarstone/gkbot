import pytest

from modules.feed.ui.keyboards.feed_added import FeedAddedMarkup


@pytest.mark.parametrize(
    "feed_url",
    [
        "https://example.com/feed.xml?tag=python&sort=new#latest",
        "https://example.com/лента.xml?tag=%D1%82%D0%B5%D1%81%D1%82",
        "https://example.com/" + "a" * 235,
        "https://example.com/" + "я" * 236,
    ],
)
def test_feed_copy_button_copies_exact_url_without_callback(feed_url: str) -> None:
    markup = FeedAddedMarkup.as_markup(feed_url)

    assert markup is not None
    assert markup.model_dump(exclude_none=True) == {
        "inline_keyboard": [
            [{"text": "Копировать URL ленты", "copy_text": {"text": feed_url}}]
        ]
    }


@pytest.mark.parametrize("feed_url", ["", "https://example.com/" + "a" * 237])
def test_feed_copy_button_omitted_outside_telegram_limit(feed_url: str) -> None:
    assert FeedAddedMarkup.as_markup(feed_url) is None
