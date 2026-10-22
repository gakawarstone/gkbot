import pytest

from modules.feed.ui.keyboards import FeedMarkup
from ui.keyboards.carousel import (
    BaseCarouselMarkup,
    CarouselMarkupButtons,
    CarouselMarkupData,
)


class CarouselMarkup(BaseCarouselMarkup[CarouselMarkupButtons, CarouselMarkupData]):
    prefix = "carousel"
    buttons = CarouselMarkupButtons
    data = CarouselMarkupData


def test_similar_is_disabled_and_item_actions_still_have_callbacks() -> None:
    markup = FeedMarkup.get_item_markup(item_id=17, feed_id=29)

    assert markup.model_dump(exclude_none=True)["inline_keyboard"] == [
        [{"text": "Похожие", "disabled": {}}],
        [
            {"text": "Оставить", "callback_data": "fd:keep:17"},
            {"text": "Убрать", "callback_data": "fd:del:17"},
        ],
    ]


@pytest.mark.parametrize(
    ("current", "length", "has_previous", "has_next"),
    [
        (0, 3, False, True),
        (1, 3, True, True),
        (2, 3, True, False),
        (0, 1, False, False),
    ],
)
def test_carousel_page_is_disabled_and_navigation_respects_boundaries(
    current: int, length: int, has_previous: bool, has_next: bool
) -> None:
    row = CarouselMarkup._get_carousel_navs_row(current, length, "42")
    buttons = [button.model_dump(exclude_none=True) for button in row]

    expected = [{"text": str(current + 1), "disabled": {}}]
    if has_previous:
        expected.insert(
            0, {"text": "<<", "callback_data": f"carousel:pkprev:{current}:42"}
        )
    if has_next:
        expected.append(
            {"text": ">>", "callback_data": f"carousel:pknext:{current}:42"}
        )
    assert buttons == expected
