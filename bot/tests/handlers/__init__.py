from configs.admins import ADMINS

INTEGRATION_TEST = 1


if INTEGRATION_TEST:
    from aiogram import Bot as _AiogramBot
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.client.telegram import TelegramAPIServer
    from aiogram.client.default import DefaultBotProperties
    from configs.env import BOT_TOKEN, API_SERVER_URL

    bot = _AiogramBot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=AiohttpSession(api=TelegramAPIServer.from_base(API_SERVER_URL)),
    )


class Bot:
    _messages = []

    async def send_message(self, *args, **kwargs):
        breakpoint()
        if INTEGRATION_TEST:
            m = await bot.send_message(*args, **kwargs)
            breakpoint()
            await m.delete()
        pass

    async def send_video(self, *args, **kwargs):
        if INTEGRATION_TEST:
            m = await bot.send_video(*args, **kwargs)
            breakpoint()
            await m.delete()
        pass

    async def send_photo(self, *args, **kwargs):
        if INTEGRATION_TEST:
            m = await bot.send_photo(*args, **kwargs)
            breakpoint()
            await m.delete()
        pass


class _FromUser:
    id = ADMINS[0]


class Event:
    from_user = _FromUser()

    def __init__(self, breakpoint_at_delete: bool = True) -> None:
        self._breakpoint_at_delete = breakpoint_at_delete

    async def delete(self):
        if self._breakpoint_at_delete:
            breakpoint()
        pass

    async def answer_photo(self, *args, **kwargs):
        breakpoint()
        pass

    async def answer_audio(self, *args, **kwargs):
        if INTEGRATION_TEST:
            _args = list(args)
            _args.insert(0, ADMINS[0])
            breakpoint()
            m = await bot.send_audio(*_args, **kwargs)
        breakpoint()
        pass

    async def answer(self, *args, **kwargs):
        if INTEGRATION_TEST:
            _args = list(args)
            _args.insert(0, ADMINS[0])
            breakpoint()
            return await bot.send_message(*_args, **kwargs)
            # await m.delete()
        breakpoint()
        pass


class CallbackEvent(Event):
    def __init__(self, callback_data: str, breakpoint_at_delete: bool = True) -> None:
        self.data = callback_data
        self.message = Event()
        super().__init__(breakpoint_at_delete)
