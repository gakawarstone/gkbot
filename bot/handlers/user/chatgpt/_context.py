from dataclasses import dataclass
from typing import Optional

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _ChatGPTContext(BaseContext):
    messages: Optional[list] = None  # BUG: list[str] not works


class ChatGPTContextManager(BaseContextManager[_ChatGPTContext]):
    props = _ChatGPTContext
