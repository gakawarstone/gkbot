from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _DownloadContext(BaseContext):
    file_name = ContextField[str](str)


class DownloadContextManager(BaseContextManager[_DownloadContext]):
    props = _DownloadContext
