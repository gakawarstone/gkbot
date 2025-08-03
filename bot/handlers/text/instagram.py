from typing import Any

from aiogram import Router, F

from services.instagram import InstagramService
from extensions.handlers.message.base import BaseHandler


# NOTE: not works at the moment, because services is not available
class InstagramPostDownloadHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        text = self.event.text or ""

        if not text:
            await self.event.answer("Не удалось распознать ссылку на пост Instagram")
            return None

        status_message = await self.event.answer(f"Скачиваю {text}")
        await self.bot.send_chat_action(self.event.chat.id, "upload_photo")
        photos = await InstagramService.get_photos_album(text)
        await self.bot.send_media_group(self.event.chat.id, list(photos))
        await status_message.delete()


def setup(r: Router):
    r.message.register(
        InstagramPostDownloadHandler, F.text.startswith("https://www.instagram.com/p/")
    )
