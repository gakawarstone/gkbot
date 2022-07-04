import aiogram

from .base import BaseMiddleware
# TODO handler(m, st, data)


class UserDataMiddleware(BaseMiddleware):
    __data = {}

    async def on_pre_process_message(self, message: aiogram.types.Message,
                                     data: dict):
        if message.from_user.id not in self.__data:
            self.__data[message.from_user.id] = {}
        print(self.__data)

        data['data'] = self.__data[message.from_user.id]
