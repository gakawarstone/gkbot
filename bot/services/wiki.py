from importlib.machinery import PathFinder
import re
from typing import Optional

import wikipedia
from wikipedia.exceptions import DisambiguationError, PageError


class WikiApi:
    @classmethod
    def __search_for_topic(cls, text: str) -> Optional[list[str]]:
        '''search primary in en wiki then in ru'''
        wikipedia.set_lang('en')
        if re.search('[а-яА-Я]', text):
            wikipedia.set_lang('ru')

        return wikipedia.search(text)

    @classmethod
    def get_quote(cls, text: str, sentences: int = 4) -> Optional[str]:
        for topic in cls.__search_for_topic(text):
            try:
                return wikipedia.summary(topic, sentences=sentences)
            except DisambiguationError:
                continue
            except PageError:
                continue
