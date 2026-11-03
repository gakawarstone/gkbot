from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _DownloadContext(BaseContext):
    file_name: Optional[str] = None


class _DownloadKeys(StrEnum):
    file_name = auto()


class DownloadContextManager(BaseContextManager[_DownloadContext, _DownloadKeys]):
    props = _DownloadContext
    keys: type[_DownloadKeys] = _DownloadKeys
