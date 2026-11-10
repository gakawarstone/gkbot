import re

import wikipedia
from wikipedia import DisambiguationError, PageError


class QuoteNotFound(Exception):
    "Couldn't find quote in wikipedia"


class WikiApi:
    @classmethod
    def __search_for_topic(cls, text: str) -> list[str] | None:
        """search primary in en wiki then in ru"""
        wikipedia.set_lang("en")
        if re.search("[а-яА-Я]", text):
            wikipedia.set_lang("ru")

        return wikipedia.search(text)

    @classmethod
    def get_quote(cls, text: str, sentences: int = 4) -> str:
        if not (topics := cls.__search_for_topic(text)):
            raise QuoteNotFound

        for topic in topics:
            try:
                return wikipedia.summary(topic, sentences=sentences)
            except (DisambiguationError, PageError):
                continue

        raise QuoteNotFound
