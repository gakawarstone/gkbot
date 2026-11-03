from abc import ABC

from aiogram.types import Message

from ..base import BaseHandler as _BaseHandler


class BaseHandler(_BaseHandler[Message], ABC):
    pass
