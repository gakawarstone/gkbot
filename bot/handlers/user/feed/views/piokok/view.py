from aiogram.types import URLInputFile

from services.gkfeed import FeedItem
from services.http import HttpService
from extensions.handlers.message.http import HttpExtension
from ui.keyboards.feed.piokok import PiokokFeedItemMarkup
from ..._base import BaseHandler
from ..video import VideoFeedItemView


class PiokokFeedItemView(VideoFeedItemView, BaseHandler, HttpExtension):
    async def _process_piokok_item(self, item: FeedItem):
        soup = await self._get_soup(item.link)

        photos = [
            await HttpService.get_redirected_url(pic.a["href"])
            # pic.a["href"]
            for pic in soup.find_all(class_="pic")
        ]
        videos = [
            # await HttpService.get_redirected_url(vid.a["href"])
            vid.a["href"]
            for vid in soup.find_all(class_="video_img")
        ]

        # breakpoint()

        if photos:
            await self.__send_piokok_item_as_corousel(item, photos[0], len(photos))
        elif videos:
            video_url = soup.find(class_="downbtn")["href"]
            # video_url = await HttpService.get_redirected_url(video_url)
            # breakpoint()
            await self._send_video(item, videos[0])
        else:
            await self._send_item(item)
        # await self._send_item(item)

    async def __send_piokok_item_as_corousel(
        self, item: FeedItem, media_url: str, media_len: int
    ):
        await self.event.answer_photo(
            URLInputFile(media_url),
            caption=f'<a href="{item.link}">Link</a>',
            reply_markup=PiokokFeedItemMarkup.get_item_markup(item.id, media_len, 0),
        )
