from urllib.parse import urlparse
from typing import Any

from configs.env import GKFEED_PASSWORD, GKFEED_USER
from services.gkfeed import GkfeedService
from ._base import BaseHandler
from ._states import FSM


class AddFeedHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        if self.event.text is None:
            raise ValueError("event.text is None after validation")

        if GKFEED_USER is None or GKFEED_PASSWORD is None:
            raise ValueError("GKFEED_USER or GKFEED_PASSWORD is not set")

        if not (
            self.event.text and urlparse(self.event.text).scheme in ["http", "https"]
        ):
            await self.event.answer("Invalid url")
            return

        gkfeed = GkfeedService(GKFEED_USER, GKFEED_PASSWORD)

        await gkfeed.add_feed_lazy(self.event.text)
        await self.event.answer(f"Feed added: {self.event.text}")
