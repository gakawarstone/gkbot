import os
import shutil
from uuid import uuid4

from settings import CACHE_DIR


class CacheDir:
    __base_path = CACHE_DIR

    def __init__(self) -> None:
        self.path = os.path.expanduser(
            self.__base_path + '/' + str(uuid4()) + '/')
        os.makedirs(self.path)

    def save_file(self, file_name: str, content: bytes) -> None:
        with open(self.path + file_name, 'wb') as f:
            f.write(content)

    def get_file_path(self, file_name: str) -> str:
        return self.path + file_name

    def delete(self) -> None:
        shutil.rmtree(self.path)
