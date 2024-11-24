from bs4 import BeautifulSoup

from typing import Any

from aiogram.types import URLInputFile

from configs.env import GKFEED_USER, GKFEED_PASSWORD
from services.http import HttpService
from services.gkfeed import GkfeedService
from extensions.handlers.message.base import BaseHandler
from ui.keyboards.feed import FeedMarkup


class GetFeedItemHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)

        items_cnt = 0
        async for item in gkfeed.get_all_user_items():
            if items_cnt > 10:
                break

            if item.link.startswith("https://www.piokok"):
                html = await HttpService.get(item.link)
                soup = BeautifulSoup(html, "html.parser")
                pics = soup.find_all(class_="pic")
                vids = soup.find_all(class_="video_img")

                photos = []
                for pic in pics:
                    photos.append(pic.a["href"])

                videos = []
                for vid in vids:
                    videos.append(vid.a["href"])

                if photos:
                    await self.event.answer_photo(
                        URLInputFile(photos[0]),
                        caption=f'<a href="{item.link}">Link</a>',
                        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
                    )

                    items_cnt += 1
                    continue

                if videos:
                    await self.event.answer_video(
                        URLInputFile(videos[0]),
                        caption=f'<a href="{item.link}">Link</a>',
                        reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
                    )

                    items_cnt += 1
                    continue

            await self.event.answer(
                f'<a href="{item.link}">Link</a>',
                reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
            )

            items_cnt += 1
