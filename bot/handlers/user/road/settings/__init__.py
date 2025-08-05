from aiogram import F, Router
from aiogram.filters import StateFilter

from ..states import FSM
from .callback import EditSettingsHandler
from .edit.get_new_setting_value import GetNewSettingValueHandler
from ui.keyboards.pomodoro import PomodoroSettingsMarkup


def setup(r: Router):
    r.callback_query.register(
        EditSettingsHandler,
        F.data.startswith(PomodoroSettingsMarkup.prefix)
    )
    r.message.register(
        GetNewSettingValueHandler,
        StateFilter(FSM.get_new_setting_value)
    )
