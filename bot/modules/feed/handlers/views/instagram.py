import base64

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.feed_parser import feed_parser
from services.gkfeed import FeedItem

from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView


class InstagramFeedItemView(BaseFeedItemView):
    async def _process_instagram_item(self, item: FeedItem) -> None:
        photo_data = await feed_parser.run(
            InstagramFeedItemView._decode_photo, item.text
        )
        caption = item.title.split("/")[-1].split(":")[1]
        photo = BufferedInputFile(photo_data, filename="image.jpg")

        await self.answer_photo(
            photo,
            caption=caption,
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    @staticmethod
    def _decode_photo(text: str) -> bytes:
        soup = BeautifulSoup(text, "html.parser")

        img_tag = soup.find("img")
        if not isinstance(img_tag, Tag):
            raise ValueError("No image tag found in the item content")  # noqa: TRY004

        src = img_tag.get("src")
        if not isinstance(src, str):
            raise ValueError("No src attribute found in the image tag")  # noqa: TRY004

        if not src.startswith("data:image"):
            raise ValueError("Image src is not a base64 data URL")

        _, encoded = src.split(",", 1)
        return base64.b64decode(encoded)
