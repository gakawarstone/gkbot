from typing import Any

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import or_f

from services.ytdlp import YtdlpDownloader
from extensions.handlers.message.base import BaseHandler

F: Message


class YtdlpShortVideoHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        status_message = await self.event.answer("Скачиваю " + self.event.text)
        await self.bot.send_chat_action(self.event.chat.id, "upload_video")
        video_file = await YtdlpDownloader.download_video(self.event.text)
        await self.event.answer_video(video_file, caption=self.event.text)
        await status_message.delete()


def setup(r: Router):
    r.message.register(
        YtdlpShortVideoHandler,
        or_f(
            F.text.startswith("https://youtube.com/shorts"),
            F.text.startswith("https://www.instagram.com/reel"),
        ),
    )
