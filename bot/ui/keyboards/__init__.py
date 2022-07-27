from settings import mng  # FIXME
from lib.keyboard_builder import KeyboardBuilder


class StartMarkup:
    @staticmethod
    def commands():
        mng.add_keyboard('f', [['test']])
        return mng.keyboards['f']


class RemindMarkup:
    @staticmethod
    def date():
        mng.add_keyboard('date', [['Сегодня', 'Завтра']],
                         placeholder='04.07.2022')
        return mng.keyboards['date']


bool_keyboard = KeyboardBuilder.add_keyboard(
    buttons=['Да', 'Нет']
)
