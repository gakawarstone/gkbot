import asyncio
import os
import shutil
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar
from uuid import uuid4

from configs.services.cache_dir import CACHE_DIR_PATH
from services.schedule import Schedule, Task


class CacheDir:
    __base_path = CACHE_DIR_PATH

    def __init__(self) -> None:
        self.path = os.path.expanduser(self.__base_path + "/" + str(uuid4()) + "/")
        os.makedirs(self.path)

    def save_file(self, file_name: str, content: bytes) -> None:
        with open(self.path + file_name, "wb") as f:
            f.write(content)

    def get_file_path(self, file_name: str) -> str:
        return self.path + file_name

    def delete(self) -> None:
        try:
            shutil.rmtree(self.path)
        except FileNotFoundError:
            pass

    async def _delete(self) -> None:
        self.delete()

    async def delete_after(self, minutes: int) -> None:
        await Schedule.run_task_after(
            Task(self._delete),
            minutes * 60,
        )


class ReadProtectedCacheDir(CacheDir):
    # Scheduled callbacks are pickled. Keep live readers shared by cache path.
    _active_readers: ClassVar[Counter[Path]] = Counter()

    @classmethod
    @contextmanager
    def reading(cls, file: Path) -> Iterator[None]:
        directory = file.parent
        cls._active_readers[directory] += 1
        try:
            yield
        finally:
            cls._active_readers[directory] -= 1
            if not cls._active_readers[directory]:
                del cls._active_readers[directory]

    async def _delete(self) -> None:
        if self._active_readers[Path(self.path)]:
            await self.delete_after(minutes=5)
            return
        await asyncio.to_thread(self.delete)
