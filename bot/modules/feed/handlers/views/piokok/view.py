from aiogram.types import URLInputFile

from services.gkfeed import FeedItem
from services.http import HttpService
from extensions.handlers.message.http import HttpExtension
from ....ui.keyboards.piokok import PiokokFeedItemMarkup
from bs4 import Tag
from ..._base import BaseHandler
from ..video import VideoFeedItemView


# NOTE: deprecated piokok not working anymore
class PiokokFeedItemView(VideoFeedItemView, BaseHandler, HttpExtension):
    async def _process_piokok_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        photos = []
        for pic in soup.find_all(class_="pic"):
            if isinstance(pic, Tag) and pic.a and pic.a.get("href"):
                photos.append(
                    await HttpService.get_redirected_url(str(pic.a.get("href")))
                )

        videos = []
        for vid in soup.find_all(class_="video_img"):
            if isinstance(vid, Tag) and vid.a and vid.a.get("href"):
                videos.append(str(vid.a.get("href")))

        if photos:
            await self.__send_piokok_item_as_carousel(item, photos[0], len(photos))
        elif videos:
            await self._send_video(item, videos[0])
        else:
            await self._send_item(item)

    async def __send_piokok_item_as_carousel(
        self, item: FeedItem, media_url: str, media_len: int
    ):
        await self.event.answer_photo(
            URLInputFile(media_url),
            caption=f'<a href="{item.link}">Link</a>',
            reply_markup=PiokokFeedItemMarkup.get_item_markup(item.id, media_len, 0),
        )
