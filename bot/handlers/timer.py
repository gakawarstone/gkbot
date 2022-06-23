import aiogram

from services.timer import Timer

data = {}


async def start(message: aiogram.types.Message):
    text = '<b>Таймер запущен</b>\n'
    text += 'Остановка таймера: /stop_timer'
    await message.answer(text)
    timer = Timer()
    timer.start()
    data['timer'] = timer


async def stop(message: aiogram.types.Message):
    try:
        timer: Timer = data['timer']
    except KeyError:
        text = '<b>Таймер не запущен</b>\n'
        text += 'Запуск таймера: /start_timer'
        await message.answer(text)
        return

    timer.stop()
    text = '<b>Таймер остановлен</b>\n'
    text += f'Начало: {timer.start_time_rfc2882}\n'
    text += f'Конец: {timer.finish_time_rfc2882}\n'
    text += f'Всего времени: <b>{timer.time_delta.strftime("%M:%S")}</b>'
    await message.answer(text)
    data.pop('timer')
