import base64

from aiogram.types import BufferedInputFile
from bs4 import BeautifulSoup, Tag

from services.gkfeed import FeedItem

from ...ui.keyboards import FeedMarkup
from .._exceptions import FeedMediaExtractionError
from . import BaseFeedItemView


class InstagramFeedItemView(BaseFeedItemView):
    async def _process_instagram_item(self, item: FeedItem) -> None:
        soup = BeautifulSoup(item.text, "html.parser")

        img_tag = soup.find("img")
        if not isinstance(img_tag, Tag):
            raise FeedMediaExtractionError("No image tag found in the item content")

        src = img_tag.get("src")
        if not isinstance(src, str):
            raise FeedMediaExtractionError("No src attribute found in the image tag")

        caption_parts = item.title.split("/")[-1].split(":")
        if len(caption_parts) < 2:
            raise FeedMediaExtractionError("Image caption not found")
        caption = caption_parts[1]

        if not src.startswith("data:image"):
            raise FeedMediaExtractionError("Image src is not a base64 data URL")

        _, separator, encoded = src.partition(",")
        if not separator:
            raise FeedMediaExtractionError("Image data URL has no payload")
        try:
            photo_data = base64.b64decode(encoded, validate=True)
        except ValueError as error:
            raise FeedMediaExtractionError("Invalid base64 image") from error
        photo = BufferedInputFile(photo_data, filename="image.jpg")

        await self.answer_photo(
            photo,
            caption=caption,
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
