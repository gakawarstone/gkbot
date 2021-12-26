from bot_config import bot
from page import Database
import aiogram
gmdb_notion_client = Database('https://www.notion.so/gakawarstone/1755f2a9e4b84d42bba313a65a40de37?v=0423839a839b4771906735f134cc40da')


async def add_test_row(message: aiogram.types.Message):
    row = gmdb_notion_client.add_row()
    row.name = 'gachi'
    row.type = 'serial'
    row.status = 'watched'
    row.progress = 's2e8'
    cv = gmdb_notion_client.get_view()
    rows = cv.collection.get_rows()
    for i in rows:
        print(i)


if __name__ == '__main__':
    bot.add_command_handler('gmdb', add_test_row)
    bot.start()
