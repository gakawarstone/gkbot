from abc import ABC, abstractmethod

import aiogram
from aiogram.dispatcher.middlewares import BaseMiddleware as Base


class BaseMiddleware(ABC, Base):
    @abstractmethod
    def on_pre_process_message(self, message: aiogram.types.Message,
                               data: dict):
        pass
