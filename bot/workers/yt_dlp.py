import os
import asyncio

from configs.services.cache_dir import CACHE_DIR_PATH
from services.cache_dir import CacheDir


class Task:
    _tasks_file_path = os.path.expanduser(CACHE_DIR_PATH + "/tasks")

    def __init__(self, url: str) -> None:
        self.url = url
        self._dir = CacheDir()
        self.id = self._dir.path.split("/")[-2]
        print(self.id)

    def create_entry(self) -> None:
        entry = f"{self.url},{self.id}\n"
        print(self._tasks_file_path)
        with open(self._tasks_file_path, "a") as f:
            f.write(entry)

    def delete_entry(self) -> None:
        with open(self._tasks_file_path, "r") as f:
            lines = f.readlines()

        target_entry = f"{self.url},{self.id}\n"
        new_lines = [line for line in lines if line != target_entry]

        with open(self._tasks_file_path, "w") as f:
            f.writelines(new_lines)

    @property
    def result(self) -> str:
        return os.path.join(self._dir.path, "video.mp4")

    @property
    def is_success(self) -> bool:
        return self._check_video_exists()

    def _check_video_exists(self) -> bool:
        video_path = os.path.join(self._dir.path, "video.mp4")
        return os.path.exists(video_path)


class YtdlpWorker:
    @classmethod
    async def download(cls, url: str) -> str:
        task = cls._build_task(url)

        for _ in range(100):
            if task.is_success:
                task.delete_entry()
                return task.result
            await asyncio.sleep(1)

        task.delete_entry()
        raise Exception("Timeout downloading: " + url)

    @classmethod
    def _build_task(cls, url: str) -> Task:
        task = Task(url)
        task.create_entry()
        return task
