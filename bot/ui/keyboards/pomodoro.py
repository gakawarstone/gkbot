from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.entities.road_settings import RoadSettings


class PomodoroSettingsMarkup:
    prefix = 'psm'

    @classmethod
    def get_settings_dialog(cls, current_settings: RoadSettings) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder(
            [
                [
                    InlineKeyboardButton(
                        text=f'Время работы: {current_settings.time_focused.minute}',
                        callback_data=f'{cls.prefix}:time_focused'
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f'Время отдыха: {current_settings.time_relax.minute}',
                        callback_data=f'{cls.prefix}:time_relax'
                    )
                ]
            ]
        ).as_markup()
