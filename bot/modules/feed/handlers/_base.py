from typing import Any
from aiogram.types import CallbackQuery

from services.gkfeed import GkfeedService, FeedItem
from services.gkfeed_auth import GkfeedAuthService
from extensions.handlers.base import BaseHandler as _ExtensionsBaseHandler
from ..ui.keyboards import FeedMarkup


class BaseHandler(_ExtensionsBaseHandler):
    async def _gkfeed(self) -> GkfeedService:
        credentials = await GkfeedAuthService().get_credentials(self.event.from_user.id)
        return GkfeedService(credentials.login, credentials.password)

    async def _send_item(self, item: FeedItem):
        if self.event.from_user is None:
            raise ValueError("from_user is required to send a message")
        await self.bot.send_message(
            self.event.from_user.id,
            f'<a href="{item.link}">{item.link.split("https://")[1].split("/")[0].split(".")[-2]}</a>',
            reply_markup=FeedMarkup.get_item_markup(item.id, item.feed_id),
        )

    async def answer(self, *args: Any, **kwargs: Any):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer")
            return await self.event.message.answer(*args, **kwargs)
        return await self.event.answer(*args, **kwargs)

    async def answer_photo(self, *args: Any, **kwargs: Any):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer_photo")
            return await self.event.message.answer_photo(*args, **kwargs)
        return await self.event.answer_photo(*args, **kwargs)

    async def answer_video(self, *args: Any, **kwargs: Any):
        if isinstance(self.event, CallbackQuery):
            if self.event.message is None:
                raise ValueError("message is required for CallbackQuery.answer_video")
            return await self.event.message.answer_video(*args, **kwargs)
        return await self.event.answer_video(*args, **kwargs)
