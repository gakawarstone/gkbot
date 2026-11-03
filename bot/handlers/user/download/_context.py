from dataclasses import dataclass
from typing import Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _DownloadContext(BaseContext):
    file_name: Optional[str] = None


class DownloadContextManager(BaseContextManager[_DownloadContext]):
    props = _DownloadContext
