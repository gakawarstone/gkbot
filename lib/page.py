from notion.block import TextBlock
from notion.client import NotionClient
from bot_config import NOTION_TOKEN
client = NotionClient(NOTION_TOKEN)


class Page(object):
    def __init__(self, URL):
        self.URL = URL

    def get_URL(self):
        return self.URL

    def get_view(self, client=client):
        """get NotionClient object"""
        return client.get_block(self.URL)

    def write(self, text):
        self.get_view().children.add_new(TextBlock, title=text)


class Database(Page):
    def get_view(self, client=client):
        """get NotionClient object"""
        return client.get_collection_view(self.URL)

    def add_row(self):
        row = self.get_view().collection.add_row()
        return row

    def get_data(self):
        pass
