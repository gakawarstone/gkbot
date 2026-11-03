from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _EditBookPropertyContext(BaseContext):
    property_name = ContextField[str](str)
    new_value = ContextField[str](str)
    book_id = ContextField[int](int)


class EditBookPropertyContextManager(BaseContextManager[_EditBookPropertyContext]):
    props = _EditBookPropertyContext
