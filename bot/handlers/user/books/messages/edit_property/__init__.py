from aiogram import Router
from aiogram.filters import StateFilter

from .get_new_value import GetNewPropertyValueHandler
from ._states import FSM


def setup(r: Router):
    r.message.register(GetNewPropertyValueHandler,
                       StateFilter(FSM.get_new_value))
