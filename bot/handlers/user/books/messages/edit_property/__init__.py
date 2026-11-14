from aiogram import Router
from aiogram.filters import StateFilter

from ._states import FSM
from .get_new_value import GetNewPropertyValueHandler


def setup(r: Router):
    r.message.register(GetNewPropertyValueHandler,
                       StateFilter(FSM.get_new_value))
