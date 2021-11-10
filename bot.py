import aiogram
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


class Form(StatesGroup):
    """
    To add state use <obj>.states.append(State())
    """
    states = []


class Bot(object):
    def __init__(self, TOKEN):
        self.__TOKEN = TOKEN
        self.__bot = self.__set_bot()
        self.dp = self.__set_dispatcher()

    def __set_bot(self):
        return aiogram.Bot(token=self.__TOKEN)

    def __set_dispatcher(self):
        storage = MemoryStorage()
        return aiogram.dispatcher.Dispatcher(self.__bot, storage=storage)

    def add_message_handler(self, func):
        """
        func(message -> aiogram.types.Message)
        """
        @self.dp.message_handler()
        async def handler(message: aiogram.types.Message):
            await func(message)

    def add_command_handler(self, command, func):
        """
        command - /<command> in telegram
        func(message -> aiogram.types.Message)
        """
        @self.dp.message_handler(commands=[command])
        async def handler(message: aiogram.types.Message):
            await func(message)

    def add_state_handler(self, state, func):
        """
        state - aiogram finite machine
        func(message -> aiogram.types.Message)
        """
        @self.dp.message_handler(state=state)
        async def handler(message: aiogram.types.Message, state: FSMContext):
            await func(message, state)

    def add_state(self):
        pass

    def start_state(self):
        pass

    def start(self):
        aiogram.utils.executor.start_polling(self.dp)
