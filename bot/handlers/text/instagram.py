from typing import Any

from aiogram import Router, F

from services.instagram import InstagramService
from extensions.handlers.message.base import BaseHandler


class InstagramPostDownloadHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        status_message = await self.event.answer("Скачиваю " + self.event.text)
        await self.bot.send_chat_action(self.event.chat.id, "upload_photo")
        photos = await InstagramService.get_photos_album(self.event.text)
        await self.bot.send_media_group(self.event.chat.id, photos)
        await status_message.delete()


def setup(r: Router):
    r.message.register(
        InstagramPostDownloadHandler, F.text.startswith("https://www.instagram.com/p/")
    )
