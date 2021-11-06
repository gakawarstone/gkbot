from bot import Bot
import aiogram
import bot_config as c


async def answer_it(message: aiogram.types.Message):
    if message["from"]["username"] == "Gakawarstone":
        await message.reply("долбаеб")


async def log_it(message: aiogram.types.Message):
    print(message)


bot = Bot(c.TOKEN)
bot.add_message_handler(log_it)

bot.start()
