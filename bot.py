import aiogram
import bot_config as config


class Bot(object):
    def __init__(self, TOKEN):
        self.__TOKEN = TOKEN
        self.dp = self.__set_dispatcher()

    def __set_dispatcher(self):
        bot = aiogram.Bot(token=self.__TOKEN)
        return aiogram.dispatcher.Dispatcher(bot)

    def __add_message_handler(self, func):
        """
        func(message -> aiogram.types.Message)
        """
        @self.dp.message_handler()
        async def handler(message: aiogram.types.Message):
            await func(message)

    def start(self):
        aiogram.utils.executor.start_polling(self.dp)


bot = Bot(config.TOKEN)
bot.start()
