from aiogram import Router
from aiogram.filters import StateFilter

from ._states import AddBookFSM as FSM
from .get_author import GetAuthorHandler
from .get_chapters_cnt import GetChaptersCnt
from .get_name import GetNameHandler


def setup(r: Router):
    r.message.register(GetNameHandler, StateFilter(FSM.get_name))
    r.message.register(GetAuthorHandler, StateFilter(FSM.get_author))
    r.message.register(GetChaptersCnt, StateFilter(FSM.get_chapters_cnt))
