from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _ChatGPTContext(BaseContext):
    messages = ContextField[list[str]](list[str])


class ChatGPTContextManager(BaseContextManager[_ChatGPTContext]):
    props = _ChatGPTContext
