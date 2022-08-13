from datetime import datetime


class TimerComponent:
    @classmethod
    def serialize_start_message(cls, timer_name: str) -> str:
        return f'Таймер {timer_name} запущен'

    @classmethod
    def serialize_data_message(cls, timer_name: str,
                               start_time_rfc2882: str,
                               finish_time_rfc2882: str,
                               time_delta: datetime) -> str:
        time_amount = time_delta.strftime('%M:%S')
        text = f'<u>Таймер {timer_name} остановлен</u>\n'
        text += f'Начало: {start_time_rfc2882}\n'
        text += f'Конец: {finish_time_rfc2882}\n'
        text += f'Всего времени: <b>{time_amount}</b>'
        return text
