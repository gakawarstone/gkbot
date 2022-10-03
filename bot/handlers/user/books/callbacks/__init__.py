from aiogram import F, Router
from aiogram.types import CallbackQuery

from ui.keyboards.books import EventsMarkup, PropertiesMarkup
from .edit_properties import EditHandler
from .events import EventsHandler

F: CallbackQuery


def setup(r: Router):
    r.callback_query.register(
        EventsHandler,
        F.data.startswith(EventsMarkup.prefix)
    )
    r.callback_query.register(
        EditHandler,
        F.data.startswith(PropertiesMarkup.prefix)
    )
