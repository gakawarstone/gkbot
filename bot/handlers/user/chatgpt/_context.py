from dataclasses import dataclass
from typing import Optional

from extensions.handlers.context_manager import BaseContextManager, BaseContext


@dataclass
class _ChatGPTContext(BaseContext):
    messages: Optional[list] = None  # BUG: list[str] not works


class ChatGPTContextManager(BaseContextManager[_ChatGPTContext]):
    props = _ChatGPTContext
