from notion.block import TextBlock
from notion_client import AsyncClient
from typing import Optional

from bot_config import NOTION_API_TOKEN
client = AsyncClient(auth=NOTION_API_TOKEN)


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

    async def get_data(self, client: AsyncClient = client,
                       filter: Optional[dict] = None) -> dict:
        id = self.URL
        if filter:
            response = await client.databases.query(database_id=id,
                                                    filter=filter)
        else:
            response = await client.databases.query(database_id=id)
        return response
