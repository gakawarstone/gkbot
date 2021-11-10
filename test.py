from bot import Bot
import aiogram
import bot_config as c


async def answer_it(message: aiogram.types.Message):
    if message["from"]["username"] == "Gakawarstone":
        await message.answer("ответь")
        print(message)


async def log_it(message: aiogram.types.Message):
    print(message)


async def sqr(message: aiogram.types.Message):
    if message["from"]["username"] == "Gakawarstone":
        await message.answer("Напиши число я возведу его в квадрат")
        a = bot.get_message()
        await message.answer(a ** 2)


bot = Bot(c.TOKEN)
bot.add_command_handler('sqr', sqr)


bot.start()
