from typing import Any
import random

import requests
from bs4 import BeautifulSoup

from configs.env import GKFEED_USER, GKFEED_PASSWORD
from extensions.handlers.message.base import BaseHandler
from ui.keyboards.feed import FeedMarkup


def _get_tag_content(item: str, tag_name: str) -> str:
    return item.split(f"<{tag_name}>")[1].split(f"</{tag_name}>")[0]


class GetFeedItemHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        html = requests.get(
            "http://feed.gws.freemyip.com/api/v1/feed",
            auth=(GKFEED_USER, GKFEED_PASSWORD),
        ).content
        soup = BeautifulSoup(html, "xml")
        items = soup.find_all("item")

        for _ in range(10):
            item = random.choice(items)
            items.remove(item)
            line = "".join(str(item).strip().split("\n"))

            try:
                await self.event.answer(
                    _get_tag_content(line, "link"),
                    reply_markup=FeedMarkup.get_item_markup(
                        int(_get_tag_content(line, "id"))
                    ),
                )
            except IndexError:
                continue
