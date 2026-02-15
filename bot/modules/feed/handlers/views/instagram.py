import base64
from bs4 import BeautifulSoup, Tag
from aiogram.types import BufferedInputFile

from services.gkfeed import FeedItem
from ...ui.keyboards import FeedMarkup
from . import BaseFeedItemView


class InstagramFeedItemView(BaseFeedItemView):
    async def _process_instagram_item(self, item: FeedItem):
        soup = BeautifulSoup(item.text, "html.parser")

        img_tag = soup.find("img")
        if not isinstance(img_tag, Tag):
            raise ValueError("No image tag found in the item content")

        src = img_tag.get("src")
        if not isinstance(src, str):
            raise ValueError("No src attribute found in the image tag")

        caption = item.title.split("/")[-1].split(":")[1]

        if not src.startswith("data:image"):
            raise ValueError("Image src is not a base64 data URL")

        _, encoded = src.split(",", 1)
        photo_data = base64.b64decode(encoded)
        photo = BufferedInputFile(photo_data, filename=f"image.jpg")

        await self.answer_photo(
            photo,
            caption=caption,
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )
