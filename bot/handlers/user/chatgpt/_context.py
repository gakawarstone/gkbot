from dataclasses import dataclass
from enum import StrEnum, auto

from extensions.handlers.context_manager import BaseContext, BaseContextManager


@dataclass
class _ChatGPTContext(BaseContext):
    messages: list[str] | None = None


class _ChatGPTKeys(StrEnum):
    messages = auto()


class ChatGPTContextManager(BaseContextManager[_ChatGPTContext, _ChatGPTKeys]):
    props = _ChatGPTContext
    keys: type[_ChatGPTKeys] = _ChatGPTKeys
