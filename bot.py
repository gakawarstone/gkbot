import aiogram
import bot_config as config


class Bot(object):
    def __init__(self, TOKEN):
        self.__TOKEN = TOKEN
        self.dp = self.__set_dispatcher()

    def __set_dispatcher(self):
        bot = aiogram.Bot(token=self.__TOKEN)
        return aiogram.dispatcher.Dispatcher(bot)

    def start(self):
        aiogram.utils.executor.start_polling(self.dp)


bot = Bot(config.TOKEN)


@bot.dp.message_handler()
async def console_log(message: aiogram.types.Message):
    print(message)

bot.start()
