from aiogram.types import URLInputFile, BufferedInputFile
from bs4 import BeautifulSoup

from services.http import HttpService
from services.gkfeed import FeedItem
from ui.keyboards.feed import FeedMarkup
from ui.keyboards.feed.piokok import PiokokFeedMarkup
from .._exceptions import UnavailableMediaException
from .._base import BaseHandler


class _PiokokCorouselWidgetExtention(BaseHandler):
    async def _send_piokok_item_as_corousel(
        self, item: FeedItem, media_url: str, media_len: int
    ):
        try:
            await self.event.answer_photo(
                URLInputFile(media_url),
                caption=f'<a href="{item.link}">Link</a>',
                reply_markup=PiokokFeedMarkup.get_item_markup(item.id, media_len, 0),
            )
        except:  # TODO: welche exception
            raise UnavailableMediaException


class PiokokFeedItemRepresentationExtention(
    _PiokokCorouselWidgetExtention, BaseHandler
):
    async def _process_piokok_item(self, item: FeedItem):
        html = await HttpService.get(item.link)
        soup = BeautifulSoup(html, "html.parser")

        try:
            photos = [pic.a["href"] for pic in soup.find_all(class_="pic")]
            if photos:
                await self._send_piokok_item_as_corousel(item, photos[0], len(photos))

            videos = [vid.a["href"] for vid in soup.find_all(class_="video_img")]
            if videos:
                await self._send_video(item, videos[0])
        except UnavailableMediaException:
            await self._send_item(item)

    async def _send_video(self, item: FeedItem, media_url: str):
        try:
            video_data = await HttpService.get(media_url)
            await self.event.answer_video(
                BufferedInputFile(video_data, "video.mp4"),
                caption=f'<a href="{item.link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )
        except:  # TODO: welche exception
            raise UnavailableMediaException
