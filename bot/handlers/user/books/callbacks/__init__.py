from aiogram import F, Router
from aiogram.types import CallbackQuery

from ui.keyboards.books import BookMarkup, BookEditMarkup
from .edit_properties import EditHandler
from .events import EventsHandler

F: CallbackQuery


def setup(r: Router):
    r.callback_query.register(
        EventsHandler,
        F.data.startswith(BookMarkup.prefix)  # [ ] filter depends on markup
    )
    # FIXME prefix_
    r.callback_query.register(
        EditHandler,
        F.data.startswith(BookEditMarkup.prefix_)  # [ ] rename editbookmarkup
    )
