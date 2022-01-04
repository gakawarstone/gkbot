from notion.block import TextBlock
from notion_client import AsyncClient
from typing import Optional

from bot_config import NOTION_API_TOKEN
client = AsyncClient(auth=NOTION_API_TOKEN)


class Page(object):
    def __init__(self, url):
        self.id = url

    def get_url(self):
        return self.id

    def get_view(self, client=client):
        """get NotionClient object"""
        return client.get_block(self.id)

    def write(self, text):
        self.get_view().children.add_new(TextBlock, title=text)


class Database(Page):
    def get_view(self, client=client):
        """get NotionClient object"""
        return client.get_collection_view(self.id)

    async def add_row(self, title: str):
        properties = {
            "Name": {"title": [{"text": {"content": title}}]}
        }
        await self.create_page(properties)

    async def create_page(self, properties):
        await client.pages.create(parent={"database_id": self.id},
                                  properties=properties)

    async def get_data(self, client: AsyncClient = client,
                       filter: Optional[dict] = None) -> dict:
        id = self.id
        if filter:
            response = await client.databases.query(database_id=id,
                                                    filter=filter)
        else:
            response = await client.databases.query(database_id=id)
        return response
