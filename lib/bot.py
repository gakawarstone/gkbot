import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


class Form(StatesGroup):
    """
    To add state use <obj>.states.append(State())
    """
    states = []


class Bot(object):
    def __init__(self, TOKEN):
        self.__bot = self.__set_bot(TOKEN)
        self.dp = self.__set_dispatcher(self.__bot)
        self.admins = []
        self.keyboards = {}
        self.inline_keyboards = {}
        self.tasks = []

    def __set_bot(self, token):
        return aiogram.Bot(token=token)

    def __set_dispatcher(self, bot):
        storage = MemoryStorage()
        return aiogram.dispatcher.Dispatcher(bot, storage=storage)

    def add_message_handler(self, func):
        """
        func(message: aiogram.types.Message)
        """
        @self.dp.message_handler()
        async def handler(message: aiogram.types.Message):
            await func(message)

    def add_command_handler(self, command, func, admin_only=False):
        """
        command - /<command> in telegram
        func(message: aiogram.types.Message)
        """
        @self.dp.message_handler(commands=[command])
        async def handler(message: aiogram.types.Message):
            is_admin = message['from']['id'] in self.admins
            if not admin_only or admin_only and is_admin:
                await func(message)

    def add_state_handler(self, state, func):
        """
        state - aiogram finite machine
        func(message: aiogram.types.Message)
        """
        @self.dp.message_handler(state=state)
        async def handler(message: aiogram.types.Message, state: FSMContext):
            await func(message, state)

    def add_keyboard(self, name, buttons, hide=True, placeholder=None):
        """
        add telegram keyboard with row of {buttons}
        call by {bot_object.keyboards[name]}
        """
        kboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                     one_time_keyboard=hide,
                                     input_field_placeholder=placeholder)
        for rows in buttons:
            kboard.row(*(KeyboardButton(i) for i in rows))
        self.keyboards[name] = kboard

    def add_url_button(self, url, text='request'):
        btn = InlineKeyboardButton(text, url=url)
        self.inline_keyboards[url] = InlineKeyboardMarkup().add(btn)
        return self.inline_keyboards[url]

    def add_task(self, func):
        self.tasks.append(func)

    async def send_message(self, id, text):
        await self.__bot.send_message(id, text)

    async def send_file(self, message, path):
        await message.answer_document(open(path, "rb"))

    async def on_startup(self, dp):
        for func in self.tasks:
            await func(dp)

    def start(self):
        executor = aiogram.utils.executor
        if self.tasks:
            executor.start_polling(self.dp, on_startup=self.on_startup)
        else:
            executor.start_polling(self.dp)
