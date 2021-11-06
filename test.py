from bot import Bot
import aiogram
import bot_config as c


def log_it(message: aiogram.types.Message):
    print(message)
    if message["from"]["username"] == "Gakawarstone":
        return message.reply("долбаеб")


bot = Bot(c.TOKEN)
bot.add_message_handler(log_it)

bot.start()
