from dataclasses import dataclass

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _DownloadContext(BaseContext):
    file_name: str | None = None


class DownloadContextManager(BaseContextManager[_DownloadContext]):
    props = _DownloadContext
