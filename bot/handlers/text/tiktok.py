from typing import Any

from aiogram import Router

from extensions.handlers.message.base import BaseHandler
from filters.tiktok import TikTokVideoLink
from services.tiktok import TikTokService
from services.tiktok.exceptions import (
    TikTokInfoExtractionFailed,
    TikTokInvalidUrl,
)
from utils.status_message import temporary_status


class TikTokVideoHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()

        link = self._tiktok_link
        async with temporary_status(self.event, f"Скачиваю {link}") as status_message:
            await self.bot.send_chat_action(self.event.chat.id, "upload_video")

            try:
                await self._send_tiktok_video(link)
            except TikTokInvalidUrl:
                await status_message.edit_text(f"Неправильная ссылка {link}")
                status_message.keep()
            except TikTokInfoExtractionFailed:
                await status_message.edit_text(f"Не получилось скачать {link}")
                status_message.keep()

    async def _send_tiktok_video(self, link: str) -> None:
        if not self.event.from_user:
            raise ValueError("Event does not have a from_user")
        from_user = self.event.from_user

        username = from_user.username if from_user.username else "user"
        caption = f'<b>{username}</b> ➤ <a href="{link.split("?")[0]}">TikTok</a>'

        video = await TikTokService.get_video(link)

        await self.event.answer_video(
            video.input_file,
            caption=caption,
            height=video.height,
            width=video.width,
            duration=video.duration,
        )

    @property
    def _tiktok_link(self) -> str:
        if not self.event.text:
            raise ValueError("TikTok link text is missing")
        return self.event.text


def setup(r: Router) -> None:
    r.message.register(TikTokVideoHandler, TikTokVideoLink())
