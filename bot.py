import aiogram
import bot_config as config


class Bot(object):
    def __init__(self, TOKEN):
        self.__TOKEN = TOKEN
        self.bot = self.__set_bot()
        self.dp = self.__set_dispatcher()

    def __set_bot(self):
        return aiogram.Bot(token=self.__TOKEN)

    def __set_dispatcher(self):
        return aiogram.dispatcher.Dispatcher(self.bot)

    def __add_message_handler(self, func):
        """
        func(message -> aiogram.types.Message)
        """
        @self.dp.message_handler()
        async def handler(message: aiogram.types.Message):
            func(message)

    def __add_command_handler(self, command, func):
        """
        command - /<command> in telegram
        func(message -> aiogram.types.Message)
        """
        @self.dp.message_handler(commands=[command])
        async def handler(message: aiogram.types.Message):
            func(message)

    def start(self):
        aiogram.utils.executor.start_polling(self.dp)


bot = Bot(config.TOKEN)
bot.start()
