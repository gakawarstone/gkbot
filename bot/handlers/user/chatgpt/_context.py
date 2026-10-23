from dataclasses import dataclass

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _ChatGPTContext(BaseContext):
    messages: list | None = None  # BUG: list[str] not works


class ChatGPTContextManager(BaseContextManager[_ChatGPTContext]):
    props = _ChatGPTContext
