from typing import Any

from aiogram import F, Router
from aiogram.types import InputMediaPhoto, MediaUnion

from extensions.handlers.message.base import BaseHandler
from services.instagram import InstagramDownloadError, InstagramService


class InstagramPostDownloadHandler(BaseHandler):
    async def handle(self) -> Any:
        await self.event.delete()
        text = self.event.text or ""

        if not text:
            await self.event.answer("Не удалось распознать ссылку на пост Instagram")
            return None

        status_message = await self.event.answer(f"Скачиваю {text}")
        await self.bot.send_chat_action(self.event.chat.id, "upload_photo")
        try:
            photos = await InstagramService.get_photos_album(text)
            await self._send_photos(photos)
            await status_message.delete()
        except InstagramDownloadError:
            await status_message.edit_text(f"Не получилось скачать {text}")

    async def _send_photos(self, photos: list[InputMediaPhoto]) -> None:
        for start in range(0, len(photos), 10):
            album: list[MediaUnion] = list(photos[start : start + 10])
            if len(album) == 1:
                await self.event.answer_photo(album[0].media)
            else:
                await self.bot.send_media_group(self.event.chat.id, album)


def setup(r: Router) -> None:
    r.message.register(
        InstagramPostDownloadHandler, F.text.startswith("https://www.instagram.com/p/")
    )
