from bot_config import bot
from datetime import datetime


def write(text):
    """
    logging {str} into log.txt
    time: {str}
    """
    with open('log.txt', 'a') as file:
        file.write(str(datetime.now()) + ': ' + text + '\n')


def clear():
    """
    clear all data from log.txt
    init title (### APP LOGS ###)
    """
    with open('log.txt', 'w') as file:
        file.write('### APP LOGS ###')


async def get(message):
    """
    send log.txt file to telegram
    """
    await bot.send_file(message, 'log.txt')
