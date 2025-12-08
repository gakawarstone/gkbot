import os
import shutil
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
        shutil.rmtree(self.path)
        del self

    async def delete_after(self, minutes: int) -> None:
        async def _delete(self) -> None:
            self.delete()

        await Schedule.run_task_after(
            Task(_delete),
            minutes * 60,
        )
