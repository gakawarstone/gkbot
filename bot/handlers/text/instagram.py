from typing import Any

from aiogram import F, Router
from aiogram.types import BufferedInputFile, InputMediaPhoto, MediaUnion

from extensions.handlers.message.base import BaseHandler
from services.instagram import InstagramDownloadError, InstagramPhoto, InstagramService


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
            photos = await InstagramService.get_photos(text)
            await self._send_photos(photos)
            await status_message.delete()
        except InstagramDownloadError:
            await status_message.edit_text(f"Не получилось скачать {text}")

    async def _send_photos(self, photos: list[InstagramPhoto]) -> None:
        for start in range(0, len(photos), 10):
            files = [
                BufferedInputFile(photo.content, filename=photo.filename)
                for photo in photos[start : start + 10]
            ]
            if len(files) == 1:
                await self.event.answer_photo(files[0])
            else:
                album: list[MediaUnion] = [
                    InputMediaPhoto(media=file) for file in files
                ]
                await self.bot.send_media_group(self.event.chat.id, album)


def setup(r: Router) -> None:
    r.message.register(
        InstagramPostDownloadHandler, F.text.startswith("https://www.instagram.com/p/")
    )
