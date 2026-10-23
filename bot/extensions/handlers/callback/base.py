from abc import ABC

from aiogram.types import CallbackQuery

from ..base import BaseHandler as _BaseHandler


class BaseHandler(_BaseHandler[CallbackQuery], ABC):
    pass
