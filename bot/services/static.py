from datetime import datetime, timedelta

from aiogram.types.input_file import FSInputFile, URLInputFile, InputFile

from configs.services.static import CACHE_STATIC_FILES
from services.http import HttpService


class _LitterboxUploader:
    host_url = "https://litterbox.catbox.moe/resources/internals/api.php"

    @classmethod
    async def upload_with_path(cls, path: str) -> str:
        file = open(path, "rb")
        try:
            data = {
                "reqtype": "fileupload",
                "fileToUpload": file,
                "time": "1h",
            }
            response = await HttpService.post(cls.host_url, body=data)
        finally:
            file.close()

        return response.decode("utf-8")


class StaticFile:
    def __init__(self, path: str, cache: bool = True):
        self.__path = path
        self.__should_cache = cache
        self.__cache_url = ""
        self.__cache_expire_timestamp = 0.0

    @property
    async def _cache_url(self) -> str:
        if datetime.now().timestamp() > self.__cache_expire_timestamp:
            self.__cache_url = await _LitterboxUploader.upload_with_path(self.__path)
            self.__cache_expire_timestamp = (
                datetime.now() + timedelta(hours=1)
            ).timestamp()
        return self.__cache_url

    async def as_str(self) -> str:
        if not self.__should_cache:
            return open(self.__path, "rb").read().decode("utf-8")
        return (await HttpService.get(await self._cache_url)).decode("utf-8")

    async def as_input_file(self) -> InputFile:
        if not CACHE_STATIC_FILES:
            return FSInputFile(self.__path)
        if not self.__should_cache:
            return FSInputFile(self.__path)
        return URLInputFile(await self._cache_url)
