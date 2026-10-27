from html import escape
from typing import Any
from urllib.parse import urlparse

from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup

from services.gkfeed import GkfeedApi, GkfeedAuthService

from ._base import BaseHandler
from ._states import FSM


class AddFeedHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        if self.event.text is None:
            raise ValueError("event.text is None after validation")

        if not (
            self.event.text and urlparse(self.event.text).scheme in ["http", "https"]
        ):
            await self.event.answer("Invalid url")
            return

        if self.event.from_user is None:
            raise ValueError("event.from_user is None")

        credentials = await GkfeedAuthService().get_credentials(self.event.from_user.id)
        gkfeed = GkfeedApi(credentials)

        await gkfeed.add_feed_lazy(self.event.text)
        markup: InlineKeyboardMarkup | None = None
        if len(self.event.text) <= 256:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Копировать URL ленты",
                            copy_text=CopyTextButton(text=self.event.text),
                        )
                    ]
                ]
            )
        await self.event.answer(
            f"Feed added: {escape(self.event.text)}", reply_markup=markup
        )
