from settings import mng  # FIXME


class RemindMarkup:
    @staticmethod
    def date():
        mng.add_keyboard('date', [['Сегодня', 'Завтра']],
                         placeholder='04.07.2022')
        return mng.keyboards['date']
