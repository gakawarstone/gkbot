from typing import Any

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest

from services.tiktok import TikTokService
from services.tiktok.exceptions import (
    TikTokInvalidUrl,
    TikTokInfoExtractionFailed,
    TikTokVideoUrlExtractionFailed,
)
from extensions.handlers.message.base import BaseHandler
from filters.tiktok import TikTokVideoLink


class TikTokVideoHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()

        link = self._tiktok_link
        status_message = await self.event.answer(f"Скачиваю {link}")
        await self.bot.send_chat_action(self.event.chat.id, "upload_video")

        try:
            await self._send_tiktok_video(link)
            await status_message.delete()
        except TikTokInvalidUrl:
            await status_message.edit_text(f"Неправильная ссылка {link}")
        except TikTokInfoExtractionFailed:
            await status_message.edit_text(f"Не получилось скачать {link}")

    async def _send_tiktok_video(self, link: str) -> None:
        if not self.event.from_user:
            raise ValueError("Event does not have a from_user")
        from_user = self.event.from_user

        username = from_user.username if from_user.username else "user"
        caption = f'<b>{username}</b> ➤ <a href="{link.split("?")[0]}">TikTok</a>'

        try:
            video_url = await TikTokService.get_video_url(link)
            await self.event.answer_video(video_url, caption=caption)
        except (TelegramBadRequest, TikTokVideoUrlExtractionFailed):
            video_file = await TikTokService.get_video_as_input_file(link)
            await self.event.answer_video(video_file, caption=caption)

    @property
    def _tiktok_link(self) -> str:
        if not self.event.text:
            raise ValueError("TikTok link text is missing")
        return self.event.text


def setup(r: Router):
    r.message.register(TikTokVideoHandler, TikTokVideoLink())
