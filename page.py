from notion.client import NotionClient
import config

client = NotionClient(config.TOKEN)


class Page(object):
    def __init__(self, URL):
        self.URL = URL
        self.block = self.__get()

    def get_URL(self):
        return self.URL

    def __get(self, client=client):
        """get NotionClient object"""
        return client.get_block(self.URL)
