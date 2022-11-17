from abc import ABC
from ._context import EditBookPropertyContextManager


class BaseHandler(EditBookPropertyContextManager, ABC):
    pass
