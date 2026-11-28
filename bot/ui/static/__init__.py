from aiogram.types.input_file import FSInputFile, InputFile, URLInputFile

from configs.services.static import CACHE_STATIC_FILES
from services.static import StaticFile as _StaticFile


class _TelegramStaticFile(_StaticFile):
    async def as_input_file(self) -> InputFile:
        if CACHE_STATIC_FILES:
            url = await self.get_cached_url()
            if url is not None:
                return URLInputFile(url)
        return FSInputFile(self.path)


class Images:
    book_shelf = _TelegramStaticFile("./static/book_shelf.png")
    road_greet = _TelegramStaticFile("./static/road_greet.png")
    sort_documents = _TelegramStaticFile("./static/sort_documents.png")
    sorted_documents = _TelegramStaticFile("./static/sorted_documents.png")


class TextFiles:
    anecdotes = _TelegramStaticFile("./static/anecdots.txt", cache=False)
