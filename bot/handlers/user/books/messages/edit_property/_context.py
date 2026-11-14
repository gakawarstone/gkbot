from extensions.handlers.context_manager import (
    BaseContext,
    BaseContextManager,
    ContextField,
)


class _EditBookPropertyContext(BaseContext):
    property_name = ContextField(str)
    new_value = ContextField(str)
    book_id = ContextField(int)


class EditBookPropertyContextManager(BaseContextManager[_EditBookPropertyContext]):
    props = _EditBookPropertyContext
